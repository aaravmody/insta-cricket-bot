import requests
import os
import json
import time
from datetime import datetime

ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
INSTAGRAM_ID = os.environ["IG_USER_ID"]

def get_todays_quiz():
    base_path = os.path.dirname(os.path.abspath(__file__))
    quiz_path = os.path.join(base_path, "cricket_quiz.txt")
    tracker_path = os.path.join(base_path, "quiz_tracker.json")
    try:
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            last_used = tracker.get("last_used_question", 0)
    except:
        last_used = 0
    with open(quiz_path, "r", encoding="utf-8") as f:
        content = f.read()
    quizzes = []
    current_number = None
    current_question = None
    current_answer = None
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(\d+)\.\s*(.*)", line)
        if match:
            if current_question and current_answer:
                quizzes.append((current_number, current_question, current_answer))
            current_number = int(match.group(1))
            current_question = match.group(2)
            current_answer = None
        elif line.startswith("Answer:"):
            current_answer = line
    if current_question and current_answer:
        quizzes.append((current_number, current_question, current_answer))
    for number, question, answer in quizzes:
        if number == last_used:
            return number, question, answer
    return None, "No quiz available", ""

def wait_for_github_pages_sync(video_url, max_attempts=30, delay=10):
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

def upload_quiz_reel():
    try:
        number, question, answer = get_todays_quiz()
    except Exception as e:
        print("❌ Failed to get today's quiz:", e)
        return False
    if not question or not answer or not number:
        print("❌ No quiz available for this reel.")
        return False
    HASHTAGS = "#cricket #quiz #cricketquiz #cricketreels #sportsreels #instacricket #cricketquestions #cricketfans #cricketlove #crickettrivia #cricketfacts #cricketworld #cricketlife #cricketcommunity #cricketaddict #cricketmania #cricketpassion #cricketdaily #cricketgram #cricketfever #cricketfunny"
    video_url = f"https://aaravmody.github.io/insta-cricket-bot/docs/output/quiz_reel_{number}.mp4"
    day_intro = f"Day {number} of 50 days 50 interesting cricket questions."
    comment_answer="Comment your answer below."
    caption = f"{day_intro}\n\n{question}\n{comment_answer}\n\n{HASHTAGS}"
    print(f"🎬 Attempting to upload: {video_url}")
    print(f"📝 Caption: {caption[:100]}...")
    if not wait_for_github_pages_sync(video_url):
        print("❌ Failed to sync with GitHub Pages")
        return False
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
        if not check_media_status(creation_id):
            print("❌ Media processing failed or timed out")
            return False
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
        print("✅ Quiz reel published successfully!")
        print(f"📋 Publish response: {publish_data}")
        return True
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Error during upload: {str(e)}")
        return False

if __name__ == "__main__":
    success = upload_quiz_reel()
    if not success:
        print("❌ Upload failed")
        exit(1)
    else:
        print("✅ Upload completed successfully") 