#!/usr/bin/env python3
import os
import datetime
import feedparser
from google.generativeai import configure, GenerativeModel

# ✅ Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ Please set the GEMINI_API_KEY environment variable")

configure(api_key=api_key)
model = GenerativeModel("gemini-1.5-flash")
SCRIPT_OUTPUT = "cricket_news_script.txt"

# ✅ RSS feed (Google News – India – Cricket)
RSS_URL = "https://news.google.com/rss/search?q=cricket&hl=en-IN&gl=IN&ceid=IN:en"

def fetch_cricket_news_from_rss():
    feed = feedparser.parse(RSS_URL)
    news_items = []

    for entry in feed.entries[:5]:
        title = entry.title.strip()
        summary = entry.summary.strip()

        # Clean out HTML tags if any (some summaries may have them)
        clean_summary = summary.replace("<b>", "").replace("</b>", "").replace("&nbsp;", " ").replace("&#39;", "'")
        news_items.append(f"• {title}. {clean_summary}")

    return "\n".join(news_items)

def generate_cricket_news_script():
    today = datetime.date.today().strftime("%B %d, %Y")
    news_text = fetch_cricket_news_from_rss()

    prompt = (
        f"Today is {today}.\n"
        "You're a cricket journalist summarizing the top 4–5 cricket stories (mostly India, but key international ones too).\n"
        "Use this raw news input:\n"
        f"{news_text}\n\n"
        "Write a 60-second news bulletin in a human, spoken tone (enthusiastic but natural). "
        "Don't include any links or suggest readers to visit any site. Just deliver the news. Begin directly with a short greeting and then dive into the news."
    )

    print("⏳ Generating today's cricket script with Gemini...")
    response = model.generate_content(prompt)
    script = response.text.strip()

    print("✅ Script generated. Writing to:", SCRIPT_OUTPUT)
    with open(SCRIPT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(script)

    print("\n🗒️ Preview:")
    print(script[:500] + ("..." if len(script) > 500 else ""))

    return script

if __name__ == "__main__":
    generate_cricket_news_script()
