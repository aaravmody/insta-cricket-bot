import requests
import os
import json
import time
from datetime import datetime

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["IG_USER_ID"]

def get_todays_comment():
    base_path = os.path.dirname(os.path.abspath(__file__))
    comments_path = os.path.join(base_path, "cricket_comments.txt")
    
    with open(comments_path, "r") as f:
        content = f.read()
    
    comments = []
    current_comment = []
    current_number = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line[0].isdigit() and line[1] == '.':
            if current_comment:
                comments.append((current_number, '\n'.join(current_comment)))
            current_number = int(line.split('.')[0])
            current_comment = [line[2:].strip()]
        else:
            current_comment.append(line)
    
    if current_comment:
        comments.append((current_number, '\n'.join(current_comment)))
    
    try:
        tracker_path = os.path.join(base_path, "message_tracker.json")
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            last_used = tracker.get("last_used_message", 0)
    except:
        last_used = 0
    
    for number, comment in comments:
        if number == last_used:
            return comment
    return "No comment available"

def upload_reel():
    today = datetime.now().strftime('%Y%m%d')
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/output/reel_{today}.mp4"
    caption = get_todays_comment()

    print("Uploading reel to Instagram...")
    create_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media"
    create_params = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": ACCESS_TOKEN
    }

    create_resp = requests.post(create_url, data=create_params).json()
    print("Create response:", create_resp)

    creation_id = create_resp.get("id")
    if not creation_id:
        print("❌ Failed to create reel container.")
        return

    print("Waiting for video processing to finish...")
    status_url = f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}"
    
    for i in range(10):  # retry up to 10 times
        time.sleep(5)
        status_resp = requests.get(status_url).json()
        status = status_resp.get("status_code")
        print(f"Check {i+1}: status = {status}")
        if status == "FINISHED":
            break
    else:
        print("❌ Media not ready after retries.")
        return

    print("Publishing reel...")
    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }
    publish_resp = requests.post(publish_url, data=publish_params).json()
    print("✅ Publish response:", publish_resp)

if __name__ == "__main__":
    upload_reel()
