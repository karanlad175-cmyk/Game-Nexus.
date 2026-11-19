from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Post, Comment, NewsletterSubscriber, ContactMessage, ArticleView, ArticleBookmark, ArticleLike
from app.schemas import CommentIn, NewsletterIn, ContactIn
from app.security import get_current_user
from app.security import get_optional_current_user
from app.schemas import (
    CommentIn,
    NewsletterIn,
    ContactIn,
    PostCreateIn,
    PostUpdateIn
)
from app.security import get_admin_user
from app.email_utils import (
    send_newsletter_welcome_email,
    send_contact_notification_email
)

router = APIRouter(prefix="/api", tags=["content"])

@router.get("/health")
def health():
    return {"status": "ok", "service": "GAME NEXUS API"}


# PUBLIC: Get the Editor's Pick article
@router.get("/featured-post")
def get_featured_post(
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(
        Post.is_published.is_(True),
        Post.is_featured.is_(True)
    ).first()

    if not post:
        return None

    return {
        "id": post.id,
        "slug": post.slug,
        "title": post.title,
        "excerpt": post.excerpt,
        "category": post.category,
        "image_path": post.image_path,
        "created_at": (
            post.created_at.isoformat()
            if post.created_at else None
        )
    }

# PUBLIC: Get a limited list of published articles
@router.get("/posts")
def list_posts(
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    posts = (
        db.query(Post)
        .filter(Post.is_published.is_(True))
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "excerpt": p.excerpt,
            "category": p.category,
            "image_path": p.image_path,
            "is_premium": p.is_premium,
            "created_at": p.created_at.isoformat()
        }
        for p in posts
    ]


# PUBLIC: Paginated article listing with search and category filters
@router.get("/posts/paginated")
def list_posts_paginated(
    page: int = Query(1, ge=1),
    per_page: int = Query(12, ge=1, le=50),
    search: str | None = Query(None, max_length=100),
    category: str | None = Query(None, max_length=80),
    db: Session = Depends(get_db)
):
    query = db.query(Post).filter(
        Post.is_published.is_(True)
    )

    if search and search.strip():
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Post.title.ilike(search_term),
                Post.excerpt.ilike(search_term),
                Post.category.ilike(search_term)
            )
        )

    if category and category.strip().lower() != "all":
        query = query.filter(
            Post.category == category.strip()
        )

    total = query.count()

    posts = (
        query
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {

        "categories": [
    category[0]
    for category in (
        db.query(Post.category)
        .filter(
            Post.is_published.is_(True),
            Post.category.isnot(None),
            Post.category != ""
        )
        .distinct()
        .order_by(Post.category)
        .all()
    )
],
        "items": [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "excerpt": p.excerpt,
                "category": p.category,
                "image_path": p.image_path,
                "is_premium": p.is_premium,
                "created_at": p.created_at.isoformat()
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    }

@router.get("/posts/{slug}")
def get_post(slug: str, db: Session = Depends(get_db)):
    post = db.query(Post).filter(
        Post.slug == slug,
        Post.is_published.is_(True)
    ).first()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found."
        )

    view = ArticleView(post_slug=slug)
    db.add(view)
    db.commit()

    return {
        "id": post.id,
        "slug": post.slug,
        "title": post.title,
        "excerpt": post.excerpt,
        "body": post.body,
        "category": post.category,
        "image_path": post.image_path,
        "is_premium": post.is_premium,
        "created_at": post.created_at.isoformat()
    }


@router.get("/most-liked-posts")
def get_most_liked_posts(db: Session = Depends(get_db)):
    results = (
        db.query(
            Post,
            func.count(ArticleLike.id).label("like_count")
        )
        .join(ArticleLike, Post.slug == ArticleLike.post_slug)
        .filter(Post.is_published.is_(True))
        .group_by(Post.id)
        .having(func.count(ArticleLike.id) > 0)
        .order_by(
            func.count(ArticleLike.id).desc(),
            Post.created_at.desc()
        )
        .limit(6)
        .all()
    )

    return [
        {
            "id": post.id,
            "slug": post.slug,
            "title": post.title, 
            "excerpt": post.excerpt,
            "category": post.category,
            "image_path": post.image_path,
            "like_count": like_count,
            "created_at": post.created_at.isoformat()
        }
        for post, like_count in results
    ]


@router.get("/trending-posts")
def get_trending_posts(db: Session = Depends(get_db)):
    results = (
        db.query(
            Post,
            func.count(ArticleView.id).label("view_count")
        )
        .outerjoin(ArticleView, Post.slug == ArticleView.post_slug)
        .filter(Post.is_published.is_(True))
        .group_by(Post.id)
        .having(func.count(ArticleView.id) > 0)
        .order_by(
            func.count(ArticleView.id).desc(),
            Post.created_at.desc()
        )
        .limit(6)
        .all()
    )

    return [
        {
            "id": post.id,
            "slug": post.slug,
            "title": post.title,
            "excerpt": post.excerpt,
            "category": post.category,
            "image_path": post.image_path,
            "view_count": view_count,
            "created_at": post.created_at.isoformat()
        }
        for post, view_count in results
    ]

@router.post("/posts/{slug}/comments", status_code=201)
def create_comment(
    slug: str,
    data: CommentIn,
    db: Session = Depends(get_db),
    current_user = Depends(get_optional_current_user)
):
    post = db.query(Post).filter(
        Post.slug == slug,
        Post.is_published.is_(True)
    ).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    comment = Comment(
        post_slug=slug,
        user_id=current_user.id if current_user else None,
        display_name=data.display_name.strip(),
        body=data.body.strip(),
        is_approved=False
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "id": comment.id,
        "display_name": comment.display_name,
        "body": comment.body,
        "is_approved": comment.is_approved,
        "message": "Comment submitted and is waiting for admin approval."
    }

@router.get("/posts/{slug}/comments")
def list_comments(slug: str, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.post_slug == slug, Comment.is_approved.is_(True)).order_by(Comment.created_at.asc()).all()
    return [{"id": c.id, "display_name": c.display_name, "body": c.body,
             "created_at": c.created_at.isoformat()} for c in comments]

@router.post("/newsletter", status_code=201)
def subscribe_newsletter(
    data: NewsletterIn,
    db: Session = Depends(get_db)
):
    email = data.email.strip().lower()

    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == email
    ).first()

    if existing:
        return {"message": "You are already subscribed."}

    subscriber = NewsletterSubscriber(email=email)

    db.add(subscriber)
    db.commit()

    try:
        send_newsletter_welcome_email(email)

    except Exception:
        import logging
        logging.exception("NEWSLETTER EMAIL ERROR")

        return {
            "message": "Subscription saved, but confirmation email could not be sent. Please check your email settings."
        }

    return {
        "message": "Subscribed successfully! A welcome email has been sent."
    }

@router.post("/contact", status_code=201)
def contact(
    data: ContactIn,
    db: Session = Depends(get_db)
):
    # Prepare contact details
    name = data.name.strip()
    sender_email = data.email.strip().lower()
    topic = data.topic.strip()
    message_text = data.message.strip()

    # Save message in PostgreSQL first
    contact_message = ContactMessage(
        name=name,
        email=sender_email,
        topic=topic,
        message=message_text
    )

    db.add(contact_message)
    db.commit()
    db.refresh(contact_message)

    # Send email notification
    try:
        send_contact_notification_email(
            name=name,
            sender_email=sender_email,
            topic=topic,
            message_text=message_text,
            rank=getattr(data, "rank", "") or ""
        )

    except Exception:
        import logging
        logging.exception(
            "GAME NEXUS CONTACT EMAIL NOTIFICATION FAILED"
        )

    return {
        "message": "Your message has been received successfully."
    }

# ADMIN: View all posts, including drafts
@router.get("/admin/posts")
def admin_list_posts(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "slug": p.slug,
            "title": p.title,
            "excerpt": p.excerpt,
            "body": p.body,
            "category": p.category,
            "image_path": p.image_path,
            "is_premium": p.is_premium,
            "is_published": p.is_published,
            "created_at": p.created_at.isoformat()
        }
        for p in posts
    ]


# ADMIN: Paginated posts with server-side search
@router.get("/admin/posts/paginated")
def admin_list_posts_paginated(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search: str = Query("", max_length=100),
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    query = db.query(Post)

    # Search posts by title, slug, excerpt, or category
    if search.strip():
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Post.title.ilike(search_term),
                Post.slug.ilike(search_term),
                Post.excerpt.ilike(search_term),
                Post.category.ilike(search_term)
            )
        )

    # Count matching posts before pagination
    total = query.count()

    # Overall dashboard statistics
    total_posts = db.query(Post).count()

    published_posts = db.query(Post).filter(
        Post.is_published.is_(True)
    ).count()

    draft_posts = db.query(Post).filter(
        Post.is_published.is_(False)
    ).count()

    # Fetch only the requested page
    posts = (
        query
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [
            {
                "id": p.id,
                "slug": p.slug,
                "title": p.title,
                "excerpt": p.excerpt,
                "body": p.body,
                "category": p.category,
                "image_path": p.image_path,
                "is_premium": p.is_premium,
                "is_published": p.is_published,
                "created_at": (
                    p.created_at.isoformat()
                    if p.created_at else None
                )
            }
            for p in posts
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "draft_posts": draft_posts
    }

# ADMIN: Create a new post
@router.post("/admin/posts", status_code=201)
def admin_create_post(
    data: PostCreateIn,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    existing = db.query(Post).filter(
        Post.slug == data.slug
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This post slug already exists."
        )

    post = Post(**data.model_dump())

    db.add(post)
    db.commit()
    db.refresh(post)

    return {
        "message": "Post created successfully.",
        "id": post.id,
        "slug": post.slug,
        "title": post.title
    }


# ADMIN: Update an existing post
@router.put("/admin/posts/{post_id}")
def admin_update_post(
    post_id: int,
    data: PostUpdateIn,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found."
        )

    existing = db.query(Post).filter(
        Post.slug == data.slug,
        Post.id != post_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This post slug already exists."
        )

    for field, value in data.model_dump().items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)

    return {"message": "Post updated successfully."}


# ADMIN: Delete a post
@router.delete("/admin/posts/{post_id}")
def admin_delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        raise HTTPException(
            status_code=404,
            detail="Post not found."
        )

    # Delete associated comments to avoid orphaned comments
    db.query(Comment).filter(
        Comment.post_slug == post.slug
    ).delete(synchronize_session=False)

    db.delete(post)
    db.commit()

    return {"message": "Post deleted successfully."}


# ADMIN: Server-side paginated comments with search and filters
@router.get("/admin/comments/paginated")
def admin_list_comments_paginated(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search: str = Query("", max_length=100),
    status: str = Query("all"),
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    query = db.query(Comment)

    # Filter by approval status
    if status == "pending":
        query = query.filter(Comment.is_approved.is_(False))
    elif status == "approved":
        query = query.filter(Comment.is_approved.is_(True))
    elif status != "all":
        raise HTTPException(
            status_code=400,
            detail="Invalid comment status."
        )

    # Search by username, article slug, or comment content
    if search.strip():
        search_term = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Comment.display_name.ilike(search_term),
                Comment.post_slug.ilike(search_term),
                Comment.body.ilike(search_term)
            )
        )

    # Count matching comments
    total = query.count()

    # Count all pending comments for dashboard display
    pending_count = db.query(Comment).filter(
        Comment.is_approved.is_(False)
    ).count()

    # Fetch only the requested page
    comments = (
        query
        .order_by(
            Comment.created_at.desc(),
            Comment.id.desc()
        )
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "items": [
            {
                "id": c.id,
                "post_slug": c.post_slug,
                "display_name": c.display_name,
                "body": c.body,
                "is_approved": c.is_approved,
                "created_at": (
                    c.created_at.isoformat()
                    if c.created_at else None
                )
            }
            for c in comments
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "pending_count": pending_count
    }


# ADMIN: View all comments, including pending comments
@router.get("/admin/comments")
def admin_list_comments(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    comments = db.query(Comment).order_by(
        Comment.created_at.desc()
    ).all()

    return [
        {
            "id": c.id,
            "post_slug": c.post_slug,
            "display_name": c.display_name,
            "body": c.body,
            "is_approved": c.is_approved,
            "created_at": c.created_at.isoformat()
        }
        for c in comments
    ]


# ADMIN: Approve a comment
@router.put("/admin/comments/{comment_id}/approve")
def admin_approve_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found."
        )

    comment.is_approved = True
    db.commit()

    return {"message": "Comment approved successfully."}


# ADMIN: Delete a comment
@router.delete("/admin/comments/{comment_id}")
def admin_delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(
            status_code=404,
            detail="Comment not found."
        )

    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted successfully."}

@router.get("/my-comments")
def get_my_comments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = (
        db.query(Comment, Post.title)
        .outerjoin(Post, Post.slug == Comment.post_slug)
        .filter(Comment.user_id == current_user.id)
        .order_by(Comment.created_at.desc())
        .all()
    )

    return [
        {
            "id": comment.id,
            "post_slug": comment.post_slug,
            "post_title": post_title or "Deleted Article",
            "body": comment.body,
            "created_at": comment.created_at.isoformat(),
            "status": "Approved" if comment.is_approved else "Pending"
        }
        for comment, post_title in results
    ]


# ADMIN: View all newsletter subscribers
@router.get("/admin/newsletter")
def admin_list_newsletter(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    subscribers = db.query(NewsletterSubscriber).order_by(
        NewsletterSubscriber.created_at.desc()
    ).all()

    return [
        {
            "id": subscriber.id,
            "email": subscriber.email,
            "created_at": subscriber.created_at.isoformat()
        }
        for subscriber in subscribers
    ]


# ADMIN: View all contact messages
@router.get("/admin/contact-messages")
def admin_list_contact_messages(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    messages = db.query(ContactMessage).order_by(
        ContactMessage.created_at.desc()
    ).all()

    return [
        {
            "id": message.id,
            "name": message.name,
            "email": message.email,
            "topic": message.topic,
            "message": message.message,
            "created_at": message.created_at.isoformat()
        }
        for message in messages
    ]


# ADMIN: Delete a contact message
@router.delete("/admin/contact-messages/{message_id}")
def admin_delete_contact_message(
    message_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    message = db.query(ContactMessage).filter(
        ContactMessage.id == message_id
    ).first()

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found."
        )

    db.delete(message)
    db.commit()

    return {"message": "Contact message deleted successfully."}


# ADMIN: Delete a newsletter subscriber
@router.delete("/admin/newsletter/{subscriber_id}")
def admin_delete_newsletter_subscriber(
    subscriber_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_user)
):
    subscriber = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.id == subscriber_id
    ).first()

    if not subscriber:
        raise HTTPException(
            status_code=404,
            detail="Newsletter subscriber not found."
        )

    db.delete(subscriber)
    db.commit()

    return {"message": "Newsletter subscriber deleted successfully."}

# -------------------------------
# ARTICLE BOOKMARKS
# -------------------------------

# Save an article
@router.post("/bookmarks/{slug}", status_code=201)
def save_bookmark(
    slug: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.slug == slug,
        Post.is_published.is_(True)
    ).first()

    if not post:
        raise HTTPException(status_code=404, detail="Article not found.")

    existing = db.query(ArticleBookmark).filter(
        ArticleBookmark.user_id == current_user.id,
        ArticleBookmark.post_slug == slug
    ).first()

    if existing:
        return {"message": "Article is already bookmarked."}

    bookmark = ArticleBookmark(
        user_id=current_user.id,
        post_slug=slug
    )

    db.add(bookmark)
    db.commit()

    return {"message": "Article bookmarked successfully."}


# Remove a saved article
@router.delete("/bookmarks/{slug}")
def remove_bookmark(
    slug: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    bookmark = db.query(ArticleBookmark).filter(
        ArticleBookmark.user_id == current_user.id,
        ArticleBookmark.post_slug == slug
    ).first()

    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found.")

    db.delete(bookmark)
    db.commit()

    return {"message": "Bookmark removed successfully."}


# Get logged-in user's saved articles

@router.get("/my-bookmarks")
def get_my_bookmarks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    results = (
        db.query(ArticleBookmark, Post)
        .join(Post, Post.slug == ArticleBookmark.post_slug)
        .filter(
            ArticleBookmark.user_id == current_user.id,
            Post.is_published.is_(True)
        )
        .order_by(ArticleBookmark.created_at.desc())
        .all()
    )

    return [
        {
            "id": post.id,
            "slug": post.slug,
            "title": post.title,
            "excerpt": post.excerpt,
            "category": post.category,
            "image_path": post.image_path,
            "saved_at": bookmark.created_at.isoformat()
        }
        for bookmark, post in results
    ]

# =========================
# ARTICLE LIKES
# =========================

@router.get("/posts/{slug}/likes")
def get_article_likes(
    slug: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.slug == slug,
        Post.is_published.is_(True)
    ).first()

    if not post:
        raise HTTPException(status_code=404, detail="Article not found.")

    total_likes = db.query(ArticleLike).filter(
        ArticleLike.post_slug == slug
    ).count()

    user_like = db.query(ArticleLike).filter(
        ArticleLike.post_slug == slug,
        ArticleLike.user_id == current_user.id
    ).first()

    return {
        "total_likes": total_likes,
        "liked_by_me": user_like is not None
    }


@router.post("/posts/{slug}/like")
def like_article(
    slug: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    post = db.query(Post).filter(
        Post.slug == slug,
        Post.is_published.is_(True)
    ).first()

    if not post:
        raise HTTPException(status_code=404, detail="Article not found.")

    existing_like = db.query(ArticleLike).filter(
        ArticleLike.post_slug == slug,
        ArticleLike.user_id == current_user.id
    ).first()

    if existing_like:
        return {"message": "Article already liked."}

    new_like = ArticleLike(
        user_id=current_user.id,
        post_slug=slug
    )

    db.add(new_like)
    db.commit()

    return {"message": "Article liked successfully."}


@router.delete("/posts/{slug}/like")
def unlike_article(
    slug: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    existing_like = db.query(ArticleLike).filter(
        ArticleLike.post_slug == slug,
        ArticleLike.user_id == current_user.id
    ).first()

    if not existing_like:
        return {"message": "Article is not liked."}

    db.delete(existing_like)
    db.commit()

    return {"message": "Article unliked successfully."}

