import os
import json
import requests
import tempfile
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_youtube(video_url, title, description, tags):
    print("🎥 Starting YouTube upload...")

    # Load credentials from GitHub Secrets
    creds = Credentials(
        None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    creds.refresh(Request())  # ✅ Fixed: Added missing Request() here

    youtube = build("youtube", "v3", credentials=creds)

    # Download video from GitHub Pages
    print("⬇️ Downloading video...")
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    r = requests.get(video_url)
    temp.write(r.content)
    temp.flush()

    # Define video metadata
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "17"  # Sports
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    # Upload to YouTube
    media = MediaFileUpload(temp.name, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⏫ Upload progress: {int(status.progress() * 100)}%")

    print(f"✅ YouTube video uploaded! Video ID: {response['id']}")
    return response['id']

def main():
    try:
        with open("message_tracker.json", "r") as f:
            tracker = json.load(f)
            message_number = tracker.get("last_used_message", 1)
            comment = tracker.get("last_used_comment", "Follow for more funny cricket moments!")
    except:
        message_number = 1
        comment = "Follow for more funny cricket moments!"

    # Short-style metadata
    title = f"Funny Cricket Moment #{message_number} #Shorts"
    description = comment + "\n\n#Shorts\nSubscribe for daily cricket laughs!"
    tags = ["cricket", "funny", "memes", "sports", "IPL", "shorts", "reels"]

    # Video URL hosted on GitHub Pages
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/docs/output/reel_{message_number}.mp4"

    upload_to_youtube(video_url, title, description, tags)

if __name__ == "__main__":
    main()
