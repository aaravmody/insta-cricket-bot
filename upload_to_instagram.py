import requests
import os
import json
import time

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["IG_USER_ID"]

base_path = os.path.dirname(os.path.abspath(__file__))
tracker_path = os.path.join(base_path, "message_tracker.json")
comments_path = os.path.join(base_path, "cricket_comments.txt")

def get_comment_by_number(target_number):
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

    for number, comment in comments:
        if number == target_number:
            return comment
    return None

def upload_reel():
    try:
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            comment_number = tracker.get("last_used_message", 0)
    except:
        comment_number = 0

    caption = get_comment_by_number(comment_number + 1)
    if not caption:
        print("❌ No comment found for current number.")
        return

    video_url = f"https://aaravmody.github.io/insta-cricket-bot/output/reel_{comment_number}.mp4"

    print(f"📤 Uploading reel {comment_number} to Instagram...")
    create_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media"
    create_params = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": ACCESS_TOKEN
    }

    create_resp = requests.post(create_url, data=create_params).json()
    print("🧾 Create response:", create_resp)

    creation_id = create_resp.get("id")
    if not creation_id:
        print("❌ Failed to create media container.")
        return

    print("⏳ Waiting for Instagram to process the reel...")
    status_url = f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ACCESS_TOKEN}"

    for i in range(10):
        time.sleep(5)
        status_resp = requests.get(status_url).json()
        status = status_resp.get("status_code")
        print(f"🔁 Check {i+1}: Status = {status}")
        if status == "FINISHED":
            break
    else:
        print("❌ Instagram did not finish processing in time.")
        return

    print("🚀 Publishing the reel...")
    publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media_publish"
    publish_params = {
        "creation_id": creation_id,
        "access_token": ACCESS_TOKEN
    }

    publish_resp = requests.post(publish_url, data=publish_params).json()
    print("✅ Publish response:", publish_resp)

    if "id" in publish_resp:
        try:
            with open(tracker_path, "w") as f:
                json.dump({"last_used_message": comment_number + 1}, f)
            print(f"📌 Updated message_tracker to {comment_number + 1}")
        except Exception as e:
            print("⚠️ Failed to update tracker:", e)
    else:
        print("❌ Publish failed, tracker not updated.")

if __name__ == "__main__":
    upload_reel()
