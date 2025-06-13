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

def wait_for_github_pages_sync(video_url, max_attempts=30, delay=10):
    """Wait for the video to be available on GitHub Pages"""
    print("⏳ Waiting for GitHub Pages to sync...")
    for attempt in range(max_attempts):
        try:
            response = requests.head(video_url)
            if response.status_code == 200:
                print("✅ GitHub Pages sync complete!")
                return True
        except:
            pass
        print(f"⏳ Check {attempt + 1}/{max_attempts}: Still syncing...")
        time.sleep(delay)
    return False

def check_media_status(creation_id, max_attempts=30, delay=10):
    """Check the status of the media processing"""
    status_url = f"https://graph.facebook.com/v19.0/{creation_id}"
    params = {"access_token": ACCESS_TOKEN}
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(status_url, params=params)
            data = response.json()
            
            if "status_code" in data:
                status = data["status_code"]
                print(f"🔁 Check {attempt + 1}: Status = {status}")
                
                if status == "FINISHED":
                    print("✅ Media processing complete!")
                    return True
                elif status == "ERROR":
                    print("❌ Media processing failed!")
                    return False
                
            time.sleep(delay)
        except Exception as e:
            print(f"⚠️ Error checking status: {str(e)}")
            time.sleep(delay)
    
    print("❌ Instagram did not finish processing in time.")
    return False

def upload_reel():
    today = datetime.now().strftime('%Y%m%d')
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/output/reel_{today}.mp4"
    caption = get_todays_comment()

    # Wait for GitHub Pages to sync
    if not wait_for_github_pages_sync(video_url):
        print("❌ Failed to sync with GitHub Pages")
        return

    # Create the media container
    print("📤 Creating media container...")
    create_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media"
    create_params = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": ACCESS_TOKEN
    }
    
    try:
        create_resp = requests.post(create_url, data=create_params).json()
        creation_id = create_resp.get("id")
        
        if not creation_id:
            print("❌ Failed to create media container:", create_resp)
            return
            
        print(f"🧾 Create response: {create_resp}")
        
        # Wait for media processing
        if not check_media_status(creation_id):
            return
            
        # Publish the reel
        print("📤 Publishing reel...")
        publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media_publish"
        publish_params = {
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN
        }
        publish_resp = requests.post(publish_url, data=publish_params).json()
        print("✅ Publish Response:", publish_resp)
        
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")

if __name__ == "__main__":
    upload_reel()
