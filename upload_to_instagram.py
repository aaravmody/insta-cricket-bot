import requests
import os
import json
from datetime import datetime

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["IG_USER_ID"]

def get_todays_comment():
    base_path = os.path.dirname(os.path.abspath(__file__))
    comments_path = os.path.join(base_path, "cricket_comments.txt")
    
    with open(comments_path, "r") as f:
        content = f.read()
    
    # Split by numbered comments (e.g., "1.", "2.", etc.)
    comments = []
    current_comment = []
    current_number = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a number followed by a dot
        if line[0].isdigit() and line[1] == '.':
            if current_comment:
                comments.append((current_number, '\n'.join(current_comment)))
            current_number = int(line.split('.')[0])
            current_comment = [line[2:].strip()]  # Remove the number and dot
        else:
            current_comment.append(line)
    
    if current_comment:
        comments.append((current_number, '\n'.join(current_comment)))
    
    # Read the last used message number
    try:
        with open(os.path.join(base_path, "message_tracker.json"), "r") as f:
            tracker = json.load(f)
            last_used = tracker.get("last_used_message", 0)
    except:
        last_used = 0
    
    # Find the current comment
    for number, comment in comments:
        if number == last_used:
            return comment
    
    return "No comment available"

def upload_reel():
    today = datetime.now().strftime('%Y%m%d')
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/output/reel_{today}.mp4"
    caption = get_todays_comment()

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
