import os
import asyncio
import edge_tts
import random
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
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            last_used = tracker.get("last_used_message", 0)
    except:
        last_used = 0

    for number, comment in comments:
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
    final_clip.write_videofile(
    output_file,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    preset="ultrafast",
    bitrate="2500k",
    threads=4,
    temp_audiofile="temp-audio.m4a",
    remove_temp=True,
    )


    os.remove(audio_path)
    if os.path.exists(text_img_path):
        os.remove(text_img_path)

    with open(tracker_path, "w") as f:
        json.dump({"last_used_message": comment_number}, f)

    print(f"✅ Reel saved to: {output_file}")
    return output_file, comment
    
    

if __name__ == "__main__":
    generate_reel()
