import os
import asyncio
import edge_tts
import random
import re
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import json

# Paths
base_path = os.path.dirname(os.path.abspath(__file__))
comments_path = os.path.join(base_path, "cricket_comments.txt")
tracker_path = os.path.join(base_path, "message_tracker.json")
background_folder = os.path.join(base_path, "background")
output_path = os.path.join(base_path, "output")
audio_path = os.path.join(base_path, "audio.mp3")
text_img_path = os.path.join(base_path, "text_overlay.png")
font_path = os.path.join(base_path, "fonts", "Montserrat-Bold.ttf")

async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
    await communicate.save(output_file)

def create_text_image(text, size=(1000, 400), max_font_size=100):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = max_font_size
    while font_size > 20:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()
        w, h = draw.multiline_textsize(text, font=font)
        if w <= size[0] - 40 and h <= size[1] - 40:
            break
        font_size -= 5

    x = (size[0] - w) // 2
    y = (size[1] - h) // 2
    draw.multiline_text((x, y), text, font=font, fill="white", align="center")
    img.save(text_img_path)
    return text_img_path

def get_next_comment():
    with open(comments_path, "r",encoding="utf-8") as f:
        content = f.read()

    comments = []
    current_comment = []
    current_number = None

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(\d+)\.\s*(.*)", line)
        if match:
            if current_comment:
                comments.append((current_number, '\n'.join(current_comment)))
            current_number = int(match.group(1))
            current_comment = [match.group(2).strip()]
        else:
            current_comment.append(line)

    if current_comment:
        comments.append((current_number, '\n'.join(current_comment)))


    if current_comment:
        comments.append((current_number, '\n'.join(current_comment)))

    # Load last used comment number
    try:
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            last_used = tracker.get("last_used_message", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        last_used = 0

    # Get the next comment
    for number, comment in sorted(comments):
        if number > last_used:
            return number, comment

    return None, "All comments have been used."


def get_random_background():
    videos = [f for f in os.listdir(background_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not videos:
        raise FileNotFoundError("No background videos found.")
    return os.path.join(background_folder, random.choice(videos))

def generate_reel():
    comment_number, comment = get_next_comment()
    if comment_number is None:
        print("🚫 All comments have been used.")
        return
    print(f"📝 Generating reel for comment #{comment_number}: {comment}")

    asyncio.run(generate_tts(comment, audio_path))
    print("🔊 TTS audio saved.")

    video_path = get_random_background()
    clip = VideoFileClip(video_path)
    if clip.duration > 30:
        start = random.uniform(0, clip.duration - 30)
        clip = clip.subclip(start, start + 30)
    clip = clip.resize((1080, 1920))

    audioclip = AudioFileClip(audio_path)
    duration = audioclip.duration

    words = comment.split()
    phrases = [' '.join(words[i:i + 3]) for i in range(0, len(words), 3)]
    phrase_duration = duration / len(phrases)
    text_clips = []

    for i, phrase in enumerate(phrases):
        start_time = i * phrase_duration
        end_time = (i + 1) * phrase_duration
        img = create_text_image(phrase)
        txt_clip = (ImageClip(img)
                    .set_duration(end_time - start_time)
                    .set_start(start_time)
                    .set_position("center"))
        text_clips.append(txt_clip)

    final_clip = CompositeVideoClip([clip] + text_clips).set_audio(audioclip)
    filename = f"reel_{comment_number}.mp4"
    output_file = os.path.join(output_path, filename)
    
    # Improved encoding settings for Instagram compatibility
    print("🎬 Encoding video for Instagram...")
    final_clip.write_videofile(
        output_file, 
        fps=30,  # Instagram prefers 30fps
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        preset="medium",  # Balance between speed and quality
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",  # Ensure compatibility
            "-crf", "23",           # Good quality
            "-maxrate", "8000k",    # Max bitrate for Instagram
            "-bufsize", "12000k",   # Buffer size
            "-movflags", "+faststart"  # Optimize for streaming
        ]
    )

    # Clean up temporary files
    os.remove(audio_path)
    if os.path.exists(text_img_path):
        os.remove(text_img_path)

    # Update tracker
    with open(tracker_path, "w") as f:
        json.dump({
            "last_used_message": comment_number,
            "last_used_comment": comment
        }, f, indent=4)


    print(f"✅ Reel saved to: {output_file}")
    
    # Verify file was created and has reasonable size
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        print(f"📊 File size: {file_size:.2f} MB")
        if file_size < 0.1:
            print("⚠️ Warning: File size seems too small")
        elif file_size > 100:
            print("⚠️ Warning: File size seems too large for Instagram")
    
    return output_file, comment

if __name__ == "__main__":
    generate_reel()