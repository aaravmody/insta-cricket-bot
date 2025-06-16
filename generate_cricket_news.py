#!/usr/bin/env python3
import os
import datetime
from google.generativeai import configure, GenerativeModel

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ Please set the GEMINI_API_KEY environment variable")

configure(api_key=api_key)

model = GenerativeModel("gemini-1.5-flash")
SCRIPT_OUTPUT = "cricket_news_script.txt"

def generate_cricket_news_script():
    today = datetime.date.today().strftime("%B %d, %Y")
    prompt = (
        f"It's {today}. You are an expert cricket news curator.\n"
        "Using web search, list and summarize the top 4–5 latest cricket stories majorly in India but also include important international cricket news.\n"
        "Write in a human tone, lasting about 60 seconds when read aloud.\n"
        "Output only the final script."
    )

    print("⏳ Fetching and curating today's cricket news with Gemini...")
    response = model.generate_content(prompt)
    script = response.text.strip()

    print("✅ Script generated. Writing to file:", SCRIPT_OUTPUT)
    with open(SCRIPT_OUTPUT, "w", encoding="utf-8") as f:
        f.write(script)

    print("\n🗒️ Preview:")
    print(script[:500] + ("..." if len(script) > 500 else ""))
    return script

if __name__ == "__main__":
    generate_cricket_news_script()
