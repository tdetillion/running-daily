import anthropic
import smtplib
import os
import json
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def get_running_news():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[
            {
                "role": "user",
                "content": (
                    "Search the web for the latest elite running news. "
                    "Prioritize the most recent stories at the top of LetsRun.com, "
                    "World Athletics, Citius Mag, and The Morning Shakeout. "
                    "Focus on: professional race results, major athlete announcements, "
                    "world records or record attempts, and upcoming elite races. "
                    "For Chicago news, use the Chicago Area Runners Association "
                    "and local running event sites. "
                    "Write exactly 4 sections, each as a short bulleted list (3-5 bullets each). "
                    "Use these exact bold headers: "
                    "**International**, **United States**, **Upcoming Races**, **Chicago Scene**. "
                    "Format each section with a bold header and bullet points using - for bullets. "
                    "Be specific — name athletes, times, and races. No fluff. "
                    "Do not include any intro sentence or preamble. Start directly with **International**."
                )
            }
        ]
    )

    news = ""
    for block in response.content:
        if block.type == "text":
            news += block.text

    return news


def parse_sections(text):
    """Parse news text into list of (header, [bullets]) tuples."""
    sections = []
    current_header = None
    current_bullets = []

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("**") and line.endswith("**"):
            if current_header:
                sections.append((current_header, current_bullets))
            current_header = line.replace("**", "")
            current_bullets = []
        elif line.startswith(("- ", "* ", "• ")):
            bullet = line.lstrip("-*• ").strip()
            if bullet:
                current_bullets.append(bullet)

    if current_header:
        sections.append((current_header, current_bullets))

    return sections


def section_to_html(header, bullets):
    bullets_html = "\n".join(
        f'      <div class="rd-bullet">{b}</div>' for b in bullets
    )
    return f"""    <div class="rd-col-head">{header}</div>
{bullets_html}"""


def generate_columns_html(sections):
    """Split 4 sections into two newspaper columns."""
    left_sections = [s for s in sections if s[0] in ("International", "Upcoming Races")]
    right_sections = [s for s in sections if s[0] in ("United States", "Chicago Scene")]

    # Fallback: split in half if headers don't match exactly
    if not left_sections and not right_sections:
        left_sections = sections[:2]
        right_sections = sections[2:]

    def render_col(secs):
        parts = []
        for i, (header, bullets) in enumerate(secs):
            if i > 0:
                parts.append('    <hr class="rd-divider">')
            parts.append(section_to_html(header, bullets))
        return "\n".join(parts)

    return f"""  <div class="rd-columns">
    <div class="rd-col">
{render_col(left_sections)}
    </div>
    <div class="rd-col">
{render_col(right_sections)}
    </div>
  </div>"""


def generate_css():
    return """@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #ede8df;
  display: flex;
  justify-content: center;
  padding: 40px 16px 80px;
}

.rd-page {
  background: #f5f0e8;
  background-image: repeating-linear-gradient(0deg, transparent, transparent 27px, rgba(0,0,0,0.04) 27px, rgba(0,0,0,0.04) 28px);
  font-family: 'Source Serif 4', serif;
  color: #1a1008;
  padding: 32px 32px 48px;
  max-width: 720px;
  width: 100%;
  border: 1px solid #c8b89a;
}

.rd-masthead {
  text-align: center;
  border-top: 4px double #1a1008;
  border-bottom: 4px double #1a1008;
  padding: 12px 0 10px;
  margin-bottom: 20px;
}

.rd-nameplate {
  font-family: 'Playfair Display', serif;
  font-size: 3rem;
  font-weight: 900;
  letter-spacing: 6px;
  text-transform: uppercase;
  color: #1a1008;
  line-height: 1;
}

.rd-nameplate span { color: #c8102e; }

.rd-masthead-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.68rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #666;
  border-top: 1px solid #1a1008;
  padding: 4px 0 0;
  margin-top: 8px;
}

.rd-masthead-meta a {
  color: #666;
  text-decoration: none;
}

.rd-masthead-meta a:hover { color: #c8102e; }

.rd-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

.rd-col {
  padding: 0 20px;
  border-right: 1px solid #c8b89a;
}

.rd-col:first-child { padding-left: 0; }
.rd-col:last-child { padding-right: 0; border-right: none; }

.rd-col-head {
  font-family: 'Playfair Display', serif;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #888;
  border-bottom: 1px solid #c8b89a;
  padding-bottom: 4px;
  margin-bottom: 10px;
}

.rd-bullet {
  font-size: 0.8rem;
  line-height: 1.5;
  padding: 4px 0 4px 12px;
  border-bottom: 1px dotted #c8b89a;
  position: relative;
  color: #2a2018;
}

.rd-bullet::before {
  content: '›';
  position: absolute;
  left: 0;
  color: #c8102e;
  font-weight: 700;
  font-size: 1rem;
  line-height: 1.3;
}

.rd-divider {
  border: none;
  border-top: 1px solid #c8b89a;
  margin: 14px 0;
}

.rd-archive-wrap {
  border-top: 2px solid #c8b89a;
  margin-top: 40px;
  padding-top: 20px;
}

.rd-archive-title {
  font-family: 'Playfair Display', serif;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #888;
  margin-bottom: 12px;
}

.rd-archive-list {
  list-style: none;
  padding: 0;
}

.rd-archive-list li {
  border-bottom: 1px dotted #c8b89a;
  padding: 7px 0;
}

.rd-archive-list a {
  font-size: 0.85rem;
  color: #1a1008;
  text-decoration: none;
  font-family: 'Source Serif 4', serif;
}

.rd-archive-list a:hover { color: #c8102e; }

.rd-back {
  display: inline-block;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #888;
  text-decoration: none;
  margin-bottom: 16px;
}

.rd-back:hover { color: #c8102e; }

@media (max-width: 560px) {
  .rd-nameplate { font-size: 2rem; letter-spacing: 3px; }
  .rd-columns { grid-template-columns: 1fr; }
  .rd-col { padding: 0; border-right: none; border-bottom: 1px solid #c8b89a; padding-bottom: 16px; margin-bottom: 16px; }
  .rd-col:last-child { border-bottom: none; }
}
"""


def generate_index_html(display_date, columns_html, archive):
    archive_items = "".join(
        f'      <li><a href="editions/{e["date"]}.html">{e["display"]}</a></li>\n'
        for e in archive
    )

    archive_block = ""
    if archive_items:
        archive_block = f"""  <div class="rd-archive-wrap">
    <div class="rd-archive-title">Past Editions</div>
    <ul class="rd-archive-list">
{archive_items}    </ul>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Running Daily</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="rd-page">
    <div class="rd-masthead">
      <div class="rd-nameplate">Running <span>&#9733;</span> Daily</div>
      <div class="rd-masthead-meta">
        <a href="https://tdetillion.github.io">tdetillion.github.io</a>
        <span>{display_date}</span>
      </div>
    </div>
{columns_html}
{archive_block}
  </div>
</body>
</html>"""


def generate_edition_html(display_date, columns_html):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Running Daily — {display_date}</title>
  <link rel="stylesheet" href="../style.css">
</head>
<body>
  <div class="rd-page">
    <div class="rd-masthead">
      <div class="rd-nameplate">Running <span>&#9733;</span> Daily</div>
      <div class="rd-masthead-meta">
        <a href="../">&#8592; All editions</a>
        <span>{display_date}</span>
      </div>
    </div>
{columns_html}
  </div>
</body>
</html>"""


def save_html_files(today_str, display_date, news_text):
    os.makedirs("editions", exist_ok=True)

    sections = parse_sections(news_text)
    columns_html = generate_columns_html(sections)

    # Save this edition page
    with open(f"editions/{today_str}.html", "w") as f:
        f.write(generate_edition_html(display_date, columns_html))

    # Load or create archive
    archive_file = "editions/archive.json"
    if os.path.exists(archive_file):
        with open(archive_file) as f:
            archive = json.load(f)
    else:
        archive = []

    entry = {"date": today_str, "display": display_date}
    if not any(e["date"] == today_str for e in archive):
        archive.insert(0, entry)
        with open(archive_file, "w") as f:
            json.dump(archive, f, indent=2)

    past = [e for e in archive if e["date"] != today_str]

    # Update index.html
    with open("index.html", "w") as f:
        f.write(generate_index_html(display_date, columns_html, past))

    # Write CSS
    with open("style.css", "w") as f:
        f.write(generate_css())

    print(f"Saved editions/{today_str}.html and updated index.html")


def send_email(news_text, display_date, today_str):
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)

    subject = f"Running Daily — {display_date}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(news_text, "plain"))

    sections = parse_sections(news_text)
    sections_html = "".join(
        f"<p><strong>{h}</strong><br>" + "<br>".join(f"› {b}" for b in bullets) + "</p>"
        for h, bullets in sections
    )

    edition_url = f"https://tdetillion.github.io/running-daily/editions/{today_str}.html"
    html = f"""<html><body style="font-family: Georgia, serif; max-width: 600px; margin: auto; padding: 20px; background: #f5f0e8;">
      <h2 style="font-family: Georgia, serif; letter-spacing: 4px; text-transform: uppercase; border-bottom: 2px solid #1a1008; padding-bottom: 8px;">Running &#9733; Daily</h2>
      <p style="color: #c8102e; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">{display_date}</p>
      <p style="font-size: 12px; margin: 8px 0 20px;"><a href="{edition_url}" style="color: #c8102e;">Read in browser →</a></p>
      <div style="line-height: 1.7; font-size: 14px; margin-top: 16px;">{sections_html}</div>
    </body></html>"""

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent to {recipient}")


if __name__ == "__main__":
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    display_date = today.strftime("%B %d, %Y")

    print("Fetching running news...")
    news = get_running_news()

    print("Sending email...")
    send_email(news, display_date, today_str)

    print("Saving HTML files...")
    save_html_files(today_str, display_date, news)

    print("Done.")
