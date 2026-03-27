import anthropic
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

def get_running_news():
    """Call Anthropic API with web search to get today's running news."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": (
                    "Search the web for elite running news from the last 48 hours. "
                    "Focus on: professional race results, major athlete announcements, "
                    "world records or record attempts, and upcoming elite races. "
                    "Sources like LetsRun.com, World Athletics, Citius Mag, and "
                    "The Morning Shakeout are ideal. "
                    "Write 2-3 paragraphs for a competitive amateur runner "
                    "who wants to stay sharp on the elite scene. "
                    "Be specific — name athletes, times, and races. No fluff."
                )
            }
        ]
    )

    # Extract the text response from content blocks
    news = ""
    for block in response.content:
        if block.type == "text":
            news += block.text

    return news



def get_html_paragraphs(text):
    paragraphs = text.strip().split("\n\n")
    return "<br><br>".join(f"<p>{p}</p>" for p in paragraphs if p.strip())

def send_email(news_text):
    """Send the news via Gmail."""
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)  # defaults to self

    today = date.today().strftime("%B %d, %Y")
    subject = f"🏃 Running Daily — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    # Plain text version
    msg.attach(MIMEText(news_text, "plain"))

    # HTML version (simple formatting)
    html = f"""
    <html><body style="font-family: Georgia, serif; max-width: 600px; margin: auto; padding: 20px;">
      <h2 style="color: #333;">🏃 Running Daily</h2>
      <p style="color: #888; font-size: 13px;">{today}</p>
      <hr style="border: 1px solid #eee;">
      <div style="line-height: 1.7; font-size: 15px;">
        {get_html_paragraphs(news_text)}
      </div>
    </body></html>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent to {recipient}")


if __name__ == "__main__":
    print("Fetching running news...")
    news = get_running_news()
    print("Sending email...")
    send_email(news)
    print("Done.")
