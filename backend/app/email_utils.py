import resend
from email.message import EmailMessage
from html import escape
from app.config import settings

def _send_email(message: EmailMessage):
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    resend.api_key = settings.resend_api_key

    plain_part = message.get_body(preferencelist=("plain",))
    html_part = message.get_body(preferencelist=("html",))

    payload = {
        "from": settings.email_from,
        "to": [message["To"]],
        "subject": message["Subject"],
    }

    if plain_part:
        payload["text"] = plain_part.get_content()

    if html_part:
        payload["html"] = html_part.get_content()

    resend.Emails.send(payload)

def send_password_reset_email(to_email: str, reset_link: str):
    message = EmailMessage()

    message["Subject"] = "GAME NEXUS - Password Reset"
    message["From"] = settings.email_from
    message["To"] = to_email

    message.set_content(
        f"""
Hello,

We received a request to reset your GAME NEXUS account password.

Click the link below to reset your password:

{reset_link}

This link will expire in 30 minutes.

If you did not request this, you can ignore this email.

Regards,
GAME NEXUS Team
"""
    )

    _send_email(message)


def send_newsletter_welcome_email(to_email: str):
    message = EmailMessage()

    message["Subject"] = "🎮 Welcome to GAME NEXUS!"
    message["From"] = settings.email_from
    message["To"] = to_email

    # Plain-text fallback
    message.set_content(
        """
Hello Gamer!

Welcome to GAME NEXUS!

You're officially part of our gaming community.

Expect the latest:
- Gaming news and updates
- Gaming guides and tips
- Esports updates
- New article announcements

Stay tuned. Your next gaming update is coming soon!

GAME NEXUS Team
"""
    )

    # Professional HTML email
    html_body = """
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#09090B;
                 font-family:Arial,Helvetica,sans-serif;color:#FAFAFA;">

      <div style="max-width:600px;margin:30px auto;padding:20px;">

        <div style="background:#121214;border:1px solid #292932;
                    border-radius:14px;overflow:hidden;">

          <div style="padding:30px 20px;text-align:center;
                      background:#18181B;border-bottom:3px solid #6366F1;">

            <h1 style="margin:0;font-size:30px;letter-spacing:2px;
                       color:#FAFAFA;">
              GAME <span style="color:#818CF8;">NEXUS</span>
            </h1>

            <p style="margin:10px 0 0;color:#A1A1AA;
                      font-size:12px;letter-spacing:3px;">
              YOUR GAMING WORLD
            </p>
          </div>

          <div style="padding:35px 28px;">

            <p style="color:#A5B4FC;font-size:13px;
                      font-weight:bold;letter-spacing:2px;">
              WELCOME TO THE COMMUNITY
            </p>

            <h2 style="font-size:27px;margin:10px 0 18px;
                       color:#FFFFFF;">
              You're officially on the list!
            </h2>

            <p style="font-size:15px;line-height:1.8;color:#D4D4D8;">
              Hello Gamer,<br><br>
              Thanks for subscribing to GAME NEXUS.
              We're excited to have you with us!
              Get ready for gaming updates, useful guides
              and the latest esports news.
            </p>

            <div style="margin:28px 0;padding:20px;
                        background:#09090B;border:1px solid #30303A;
                        border-radius:10px;">

              <h3 style="margin:0 0 15px;color:#A5B4FC;
                         font-size:16px;">
                WHAT'S COMING YOUR WAY
              </h3>

              <p style="color:#E4E4E7;font-size:14px;
                        line-height:2;margin:0;">
                🎮 Latest gaming news<br>
                ⚡ Gaming tips and guides<br>
                🏆 Esports updates<br>
                🔥 New article announcements
              </p>
            </div>

            <p style="font-size:14px;line-height:1.7;color:#A1A1AA;">
              Stay tuned. Your next gaming update is coming soon!
            </p>

            <div style="margin-top:30px;border-top:1px solid #30303A;
                        padding-top:20px;">
              <p style="font-size:14px;color:#D4D4D8;">
                Stay sharp. Stay competitive.
              </p>
              <p style="font-size:14px;font-weight:bold;color:#818CF8;">
                — TEAM GAME NEXUS
              </p>
            </div>

          </div>
        </div>

        <p style="text-align:center;color:#71717A;
                  font-size:11px;margin-top:20px;">
          You received this email because you subscribed
          to the GAME NEXUS newsletter.
        </p>

      </div>
    </body>
    </html>
    """

    message.add_alternative(html_body, subtype="html")

    _send_email(message)

def send_newsletter_campaign_email(
    to_email: str,
    subject: str,
    campaign_message: str
):
    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = to_email

    message.set_content(
        f"""
Hello Gamer!

{campaign_message}

Stay connected with GAME NEXUS for the latest gaming updates.

Happy Gaming!
GAME NEXUS Team
"""
    )

    safe_subject = escape(subject)
    safe_message = escape(campaign_message).replace("\n", "<br>")

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="
        margin:0;
        padding:30px 15px;
        background:#09090B;
        font-family:Arial,sans-serif;
        color:#FAFAFA;
    ">
        <div style="
            max-width:600px;
            margin:auto;
            background:#121214;
            border:1px solid #27272A;
            border-radius:12px;
            padding:30px;
        ">
            <h1 style="color:#6366F1;">
                GAME NEXUS
            </h1>

            <h2>{safe_subject}</h2>

            <div style="
                color:#D4D4D8;
                font-size:15px;
                line-height:1.8;
            ">
                {safe_message}
            </div>

            <hr style="border-color:#27272A;margin:25px 0;">

            <p style="color:#A1A1AA;">
                Stay connected. Stay ahead. Happy Gaming!
            </p>

            <strong style="color:#6366F1;">
                GAME NEXUS Team
            </strong>
        </div>
    </body>
    </html>
    """

    message.add_alternative(html_body, subtype="html")

    _send_email(message)

def send_contact_notification_email(
    name: str,
    sender_email: str,
    topic: str,
    message_text: str,
    rank: str = ""
):
    message = EmailMessage()

    # Send notification to your configured Gmail account
    message["Subject"] = f"GAME NEXUS - New Contact Message: {topic}"
    message["From"] = settings.email_from
    message["To"] = settings.email_username
    message["Reply-To"] = sender_email

    rank_text = rank.strip() if rank else "Not provided"

    # Plain-text email
    message.set_content(
        f"""
Hello GAME NEXUS Admin,

You have received a new message through your website contact form.

CONTACT DETAILS
------------------------------
Name: {name}
Email: {sender_email}
Topic: {topic}
Rank: {rank_text}

MESSAGE
------------------------------
{message_text}

You can reply directly to this email to contact the sender.

Regards,
GAME NEXUS Website
"""
    )

    # HTML email
    safe_name = escape(name)
    safe_email = escape(sender_email)
    safe_topic = escape(topic)
    safe_rank = escape(rank_text)
    safe_message = escape(message_text).replace("\n", "<br>")

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="
        margin:0;
        padding:30px 15px;
        background:#09090B;
        font-family:Arial,sans-serif;
        color:#FAFAFA;
    ">
        <div style="
            max-width:600px;
            margin:auto;
            background:#121214;
            border:1px solid #303036;
            border-radius:12px;
            overflow:hidden;
        ">
            <div style="
                padding:25px;
                background:#18181B;
                border-bottom:3px solid #ff4b2b;
            ">
                <h1 style="margin:0;color:#fff;">
                    GAME <span style="color:#ff4b2b;">NEXUS.</span>
                </h1>
                <p style="color:#A1A1AA;margin-bottom:0;">
                    NEW WEBSITE CONTACT MESSAGE
                </p>
            </div>

            <div style="padding:28px;">

                <h2 style="color:#ff4b2b;">
                    New Contact Submission
                </h2>

                <table style="
                    width:100%;
                    border-collapse:collapse;
                    color:#E4E4E7;
                    font-size:14px;
                ">
                    <tr>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            <strong>Name</strong>
                        </td>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            {safe_name}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            <strong>Email</strong>
                        </td>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            {safe_email}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            <strong>Topic</strong>
                        </td>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            {safe_topic}
                        </td>
                    </tr>

                    <tr>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            <strong>Rank</strong>
                        </td>
                        <td style="padding:10px;border-bottom:1px solid #303036;">
                            {safe_rank}
                        </td>
                    </tr>
                </table>

                <h3 style="color:#ff4b2b;margin-top:28px;">
                    Message
                </h3>

                <div style="
                    padding:18px;
                    background:#09090B;
                    border:1px solid #303036;
                    border-radius:8px;
                    color:#D4D4D8;
                    font-size:14px;
                    line-height:1.8;
                    overflow-wrap:anywhere;
                ">
                    {safe_message}
                </div>

                <p style="
                    margin-top:25px;
                    color:#A1A1AA;
                    font-size:13px;
                ">
                    You can reply directly to this email to contact
                    the person who submitted this message.
                </p>

                <p style="color:#ff4b2b;font-weight:bold;">
                    GAME NEXUS Team
                </p>

            </div>
        </div>
    </body>
    </html>
    """

    message.add_alternative(html_body, subtype="html")
_send_email(message)