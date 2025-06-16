import requests
import os
import time

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["IG_USER_ID"]

VIDEO_FILENAME = "reel_news.mp4"
VIDEO_PATH = os.path.join(os.path.dirname(__file__), "output", VIDEO_FILENAME)
VIDEO_URL = f"https://aaravmody.github.io/insta-cricket-bot/docs/output/{VIDEO_FILENAME}"

HASHTAGS = "#cricket #indiancricketnews #ipl #cricketnews #cricketreels #sportsreels #instacricket #updates #latestnews #cricketmemes #cricketlovers #cricketupdates #cricbuzz #cricketvideos"

CAPTION = f"🗞️ Catch the latest cricket news update!\n\n{HASHTAGS}"

def wait_for_github_pages_sync(video_url, max_attempts=30, delay=10):
    print("⏳ Waiting for GitHub Pages to sync...")
    for attempt in range(max_attempts):
        try:
            response = requests.head(video_url, timeout=10)
            if response.status_code == 200:
                print("✅ GitHub Pages sync complete!")
                return True
        except:
            pass
        print(f"🔄 Check {attempt + 1}/{max_attempts}...")
        time.sleep(delay)
    return False

def check_media_status(creation_id):
    url = f"https://graph.facebook.com/v19.0/{creation_id}"
    for _ in range(60):
        response = requests.get(url, params={"access_token": ACCESS_TOKEN, "fields": "status_code"})
        data = response.json()
        if data.get("status_code") == "FINISHED":
            print("✅ Media processing complete!")
            return True
        elif data.get("status_code") == "ERROR":
            print("❌ Media processing failed.")
            return False
        time.sleep(10)
    print("❌ Timeout waiting for media processing.")
    return False

def upload_news_reel():
    print(f"📤 Uploading news reel: {VIDEO_FILENAME}")
    print(f"🎥 Video URL: {VIDEO_URL}")
    print(f"📝 Caption: {CAPTION[:100]}...")

    if not wait_for_github_pages_sync(VIDEO_URL):
        print("❌ GitHub Pages did not sync in time.")
        return False

    container_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media"
    container_params = {
        "video_url": VIDEO_URL,
        "caption": CAPTION,
        "media_type": "REELS",
        "access_token": ACCESS_TOKEN
    }

    response = requests.post(container_url, data=container_params)
    if response.status_code != 200:
        print(f"❌ Failed to create media container: {response.text}")
        return False

    creation_id = response.json().get("id")
    if not creation_id:
        print("❌ No creation ID returned.")
        return False

    if not check_media_status(creation_id):
        return False

    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }

    publish_resp = requests.post(publish_url, data=publish_params)
    if publish_resp.status_code == 200:
        print("✅ News reel published successfully!")
        return True
    else:
        print(f"❌ Failed to publish: {publish_resp.text}")
        return False

if __name__ == "__main__":
    success = upload_news_reel()
    exit(0 if success else 1)
