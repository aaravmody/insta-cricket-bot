import requests
from datetime import datetime

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["IG_USER_ID"]

def upload_reel():
    today = datetime.now().strftime('%Y%m%d')
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/output/reel_{today}.mp4"
    caption = "Your funny cricket comment here #cricket"

    create_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media"
    create_params = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": ACCESS_TOKEN
    }
    create_resp = requests.post(create_url, data=create_params).json()
    creation_id = create_resp.get("id")

    if not creation_id:
        print("Failed to create reel:", create_resp)
        return

    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    publish_resp = requests.post(publish_url, data=publish_params).json()
    print("Publish Response:", publish_resp)

if __name__ == "__main__":
    upload_reel()
