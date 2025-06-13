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
            response = requests.head(video_url, timeout=30)
            if response.status_code == 200:
                print("✅ GitHub Pages sync complete!")
                return True
        except Exception as e:
            print(f"⚠️ Sync check error: {str(e)}")
        print(f"⏳ Check {attempt + 1}/{max_attempts}: Still syncing...")
        time.sleep(delay)
    return False

def check_media_status(creation_id, max_attempts=60, delay=15):
    """Check the status of the media processing - increased timeout"""
    status_url = f"https://graph.facebook.com/v19.0/{creation_id}"
    params = {"access_token": ACCESS_TOKEN, "fields": "status_code,status"}
    
    print(f"🔄 Starting media processing check (max {max_attempts * delay / 60:.1f} minutes)...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(status_url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"⚠️ API returned status {response.status_code}: {response.text}")
                time.sleep(delay)
                continue
                
            data = response.json()
            print(f"🔍 Raw response: {data}")
            
            if "status_code" in data:
                status = data["status_code"]
                print(f"🔁 Check {attempt + 1}/{max_attempts}: Status = {status}")
                
                if status == "FINISHED":
                    print("✅ Media processing complete!")
                    return True
                elif status == "ERROR":
                    print("❌ Media processing failed!")
                    print(f"Error details: {data}")
                    return False
                elif status in ["IN_PROGRESS", "PUBLISHED"]:
                    print(f"🔄 Status: {status} - continuing to wait...")
                else:
                    print(f"🤔 Unknown status: {status}")
                
            else:
                print(f"⚠️ No status_code in response: {data}")
                
            time.sleep(delay)
            
        except requests.exceptions.Timeout:
            print(f"⏰ Request timeout on attempt {attempt + 1}")
            time.sleep(delay)
        except Exception as e:
            print(f"⚠️ Error checking status (attempt {attempt + 1}): {str(e)}")
            time.sleep(delay)
    
    print("❌ Instagram did not finish processing in time.")
    return False

def upload_reel():
    # Get the current message number from tracker
    try:
        with open("message_tracker.json", "r") as f:
            tracker = json.load(f)
            message_number = tracker.get("last_used_message", 1)
    except:
        message_number = 1
    
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/output/reel_{message_number}.mp4"
    caption = get_todays_comment()

    print(f"🎬 Attempting to upload: {video_url}")
    print(f"📝 Caption: {caption[:100]}...")

    # Wait for GitHub Pages to sync
    if not wait_for_github_pages_sync(video_url):
        print("❌ Failed to sync with GitHub Pages")
        return False

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
        print("🔗 Making request to Instagram API...")
        create_resp = requests.post(create_url, data=create_params, timeout=60)
        
        if create_resp.status_code != 200:
            print(f"❌ Create request failed with status {create_resp.status_code}")
            print(f"Response: {create_resp.text}")
            return False
            
        create_data = create_resp.json()
        creation_id = create_data.get("id")
        
        if not creation_id:
            print("❌ Failed to create media container:", create_data)
            return False
            
        print(f"✅ Media container created with ID: {creation_id}")
        print(f"🧾 Full create response: {create_data}")
        
        # Wait for media processing with longer timeout
        if not check_media_status(creation_id):
            print("❌ Media processing failed or timed out")
            return False
            
        # Publish the reel
        print("📤 Publishing reel...")
        publish_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ID}/media_publish"
        publish_params = {
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN
        }
        
        publish_resp = requests.post(publish_url, data=publish_params, timeout=60)
        
        if publish_resp.status_code != 200:
            print(f"❌ Publish request failed with status {publish_resp.status_code}")
            print(f"Response: {publish_resp.text}")
            return False
            
        publish_data = publish_resp.json()
        print("✅ Reel published successfully!")
        print(f"📋 Publish response: {publish_data}")
        return True
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")
        return False

if __name__ == "__main__":
    success = upload_reel()
    if not success:
        print("❌ Upload failed")
        exit(1)
    else:
        print("✅ Upload completed successfully")