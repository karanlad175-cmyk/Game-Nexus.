
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db, SessionLocal
from app.models import (
    User,
    Post,
    Comment,
    NewsletterSubscriber,
    ContactMessage,
    ArticleView,
    NewsletterCampaign
)
from app.security import get_admin_user
from pydantic import BaseModel, Field
from app.email_utils import send_newsletter_campaign_email

router = APIRouter(prefix="/api/admin", tags=["admin"])

class NewsletterCampaignIn(BaseModel):
    subject: str = Field(min_length=3, max_length=150)
    body: str = Field(min_length=5, max_length=10000)


# -------------------------------
# MANAGE USERS
# -------------------------------

@router.get("/users")
def admin_list_users(
    search: str = Query(default="", max_length=100),
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    query = db.query(User)

    if search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.email.ilike(term)) |
            (User.gamer_tag.ilike(term))
        )

    users = query.order_by(User.created_at.desc()).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "gamer_tag": user.gamer_tag,
            "is_admin": user.is_admin,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at else None
            )
        }
        for user in users
    ]


# -------------------------------
# DASHBOARD ANALYTICS
# -------------------------------

@router.get("/analytics")
def admin_analytics(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    # Total statistics
    total_users = db.query(User).count()
    total_posts = db.query(Post).count()

    published_posts = db.query(Post).filter(
        Post.is_published == True
    ).count()

    draft_posts = db.query(Post).filter(
        Post.is_published == False
    ).count()

    total_comments = db.query(Comment).count()

    approved_comments = db.query(Comment).filter(
        Comment.is_approved == True
    ).count()

    pending_comments = db.query(Comment).filter(
        Comment.is_approved == False
    ).count()

    total_subscribers = db.query(
        NewsletterSubscriber
    ).count()

    total_messages = db.query(ContactMessage).count()
        # Article view statistics
    total_article_views = db.query(ArticleView).count()

    popular_posts = db.query(
        Post.title,
        Post.slug,
        func.count(ArticleView.id).label("views")
    ).outerjoin(
        ArticleView,
        ArticleView.post_slug == Post.slug
    ).group_by(
        Post.id,
        Post.title,
        Post.slug
    ).order_by(
        func.count(ArticleView.id).desc(),
        Post.title.asc()
    ).limit(5).all()

    popular_posts_data = [
        {
            "title": post.title,
            "slug": post.slug,
            "views": post.views
        }
        for post in popular_posts
    ]

    # Monthly user registrations (last 6 months)
    now = datetime.now(timezone.utc)

    current_month = datetime(
        now.year, now.month, 1,
        tzinfo=timezone.utc
    )

    monthly_registrations = []

    for i in range(5, -1, -1):
        month_number = current_month.month - i
        year = current_month.year

        while month_number <= 0:
            month_number += 12
            year -= 1

        month_start = datetime(
            year, month_number, 1,
            tzinfo=timezone.utc
        )

        if month_number == 12:
            next_month = datetime(
                year + 1, 1, 1,
                tzinfo=timezone.utc
            )
        else:
            next_month = datetime(
                year, month_number + 1, 1,
                tzinfo=timezone.utc
            )

        count = db.query(User).filter(
            User.created_at >= month_start,
            User.created_at < next_month
        ).count()

        monthly_registrations.append({
            "month": month_start.strftime("%b %Y"),
            "registrations": count
        })

    return {
        "total_users": total_users,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "draft_posts": draft_posts,
        "total_comments": total_comments,
        "approved_comments": approved_comments,
        "pending_comments": pending_comments,
        "total_subscribers": total_subscribers,
        "total_messages": total_messages,
        "total_article_views": total_article_views,
        "popular_posts": popular_posts_data,
        "monthly_registrations": monthly_registrations
    }

# -------------------------------
# SEND NEWSLETTER CAMPAIGN
# -------------------------------

def process_newsletter_campaign(
    campaign_id,
    emails,
    subject,
    body
):
    campaign_db = SessionLocal()

    sent = 0
    failed = 0

    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(
                    send_newsletter_campaign_email,
                    email,
                    subject,
                    body
                )
                for email in emails
            ]

            for future in as_completed(futures):
                try:
                    future.result()
                    sent += 1
                except Exception:
                    logging.exception(
                        "Newsletter campaign email failed."
                    )
                    failed += 1

        campaign = campaign_db.query(
            NewsletterCampaign
        ).filter(
            NewsletterCampaign.id == campaign_id
        ).first()

        if campaign:
            campaign.sent_count = sent
            campaign.failed_count = failed

            if failed == 0:
                campaign.status = "Completed"
            elif sent == 0:
                campaign.status = "Failed"
            else:
                campaign.status = "Completed with errors"

            campaign.completed_at = datetime.now(timezone.utc)

            campaign_db.commit()

        logging.info(
            "Campaign %s finished: sent=%s failed=%s",
            campaign_id,
            sent,
            failed
        )

    except Exception:
        campaign_db.rollback()
        logging.exception("Campaign processing failed.")

    finally:
        campaign_db.close()


@router.post("/newsletter/send")
def send_newsletter_campaign(
    data: NewsletterCampaignIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    subject = data.subject.strip()
    body = data.body.strip()

    if "\n" in subject or "\r" in subject:
        raise HTTPException(
            status_code=400,
            detail="Invalid email subject."
        )

    if not subject or not body:
        raise HTTPException(
            status_code=400,
            detail="Subject and message are required."
        )

    emails = [
        subscriber.email
        for subscriber in db.query(NewsletterSubscriber).all()
    ]

    if not emails:
        return {
            "message": "No newsletter subscribers found.",
            "total": 0
        }

    campaign = NewsletterCampaign(
        subject=subject,
        body=body,
        total_recipients=len(emails),
        sent_count=0,
        failed_count=0,
        status="Processing"
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    background_tasks.add_task(
        process_newsletter_campaign,
        campaign.id,
        emails,
        subject,
        body
    )

    return {
        "message": "Newsletter campaign started.",
        "total": len(emails),
        "campaign_id": campaign.id,
        "status": "Processing"
    }

# -------------------------------
# SEND TEST NEWSLETTER EMAIL
# -------------------------------

@router.post("/newsletter/test")
def send_newsletter_test(
    data: NewsletterCampaignIn,
    background_tasks: BackgroundTasks,
    admin=Depends(get_admin_user)
):
    subject = data.subject.strip()
    body = data.body.strip()

    if "\n" in subject or "\r" in subject:
        raise HTTPException(
            status_code=400,
            detail="Invalid email subject."
        )

    if not subject or not body:
        raise HTTPException(
            status_code=400,
            detail="Subject and message are required."
        )

    if not admin.email:
        raise HTTPException(
            status_code=400,
            detail="Admin email address not found."
        )

    background_tasks.add_task(
        send_newsletter_campaign_email,
        admin.email,
        subject,
        body
    )

    return {
        "message": "Test email has been queued successfully.",
        "recipient": admin.email
    }

# -------------------------------
# NEWSLETTER CAMPAIGN HISTORY
# -------------------------------

@router.get("/newsletter/history")
def get_newsletter_campaign_history(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    campaigns = db.query(
        NewsletterCampaign
    ).order_by(
        NewsletterCampaign.created_at.desc()
    ).all()

    return [
        {
            "id": campaign.id,
            "subject": campaign.subject,
            "body": campaign.body,
            "total_recipients": campaign.total_recipients,
            "sent_count": campaign.sent_count,
            "failed_count": campaign.failed_count,
            "status": campaign.status,
            "created_at": (
                campaign.created_at.isoformat()
                if campaign.created_at else None
            ),
            "completed_at": (
                campaign.completed_at.isoformat()
                if campaign.completed_at else None
            )
        }
        for campaign in campaigns
    ]


# -------------------------------
# EDITOR'S PICK MANAGEMENT
# -------------------------------

@router.get("/featured/options")
def get_featured_options(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    posts = db.query(Post).filter(
        Post.is_published.is_(True)
    ).order_by(Post.created_at.desc()).all()

    return [
        {
            "id": post.id,
            "slug": post.slug,
            "title": post.title,
            "image_path": post.image_path,
            "is_featured": post.is_featured
        }
        for post in posts
    ]


@router.post("/featured/{post_id}")
def set_featured_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.is_published.is_(True)
    ).first()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Published article not found."
        )

    # Remove featured status from all previous articles
    db.query(Post).update(
        {Post.is_featured: False},
        synchronize_session=False
    )

    # Select the new Editor's Pick
    post.is_featured = True

    db.commit()
    db.refresh(post)

    return {
        "message": "Editor's Pick updated successfully.",
        "id": post.id,
        "slug": post.slug,
        "title": post.title
    }
