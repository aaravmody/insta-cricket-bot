import os
import asyncio
import edge_tts
import random
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import json

# Paths
base_path = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(base_path, "cricket_news_script.txt")
tracker_path = os.path.join(base_path, "message_tracker.json")
background_folder = os.path.join(base_path, "background")
output_path = os.path.join(base_path, "output")
audio_path = os.path.join(base_path, "audio.mp3")
text_img_path = os.path.join(base_path, "text_overlay.png")
font_path = os.path.join(base_path, "fonts", "Montserrat-Bold.ttf")

# Use a better, natural sounding voice (Edge TTS)
VOICE = "en-US-GuyNeural"

async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, VOICE)
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

def get_news_script():
    with open(script_path, "r", encoding="utf-8") as f:
        news = f.read().strip()

    try:
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            if tracker.get("last_used_script") == news:
                print("🚫 Already used this script.")
                return None
    except:
        pass

    return news

def get_random_background():
    videos = [f for f in os.listdir(background_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not videos:
        raise FileNotFoundError("No background videos found.")
    return os.path.join(background_folder, random.choice(videos))

def loop_background(clip, duration_needed):
    """Loop the background clip to match or exceed the duration needed."""
    if clip.duration >= duration_needed:
        return clip.subclip(0, duration_needed)

    loops = int(duration_needed // clip.duration) + 1
    looped = concatenate_videoclips([clip] * loops)
    return looped.subclip(0, duration_needed)

def generate_reel():
    script = get_news_script()
    if not script:
        return

    print(f"📝 Generating reel for script:\n{script[:150]}...\n")

    asyncio.run(generate_tts(script, audio_path))
    print("🔊 TTS audio saved.")

    audioclip = AudioFileClip(audio_path)
    duration = audioclip.duration

    video_path = get_random_background()
    bg_clip = VideoFileClip(video_path).resize((1080, 1920))
    clip = loop_background(bg_clip, duration)

    words = script.split()
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
    filename = f"reel_news.mp4"
    output_file = os.path.join(output_path, filename)

    print("🎬 Encoding video for Instagram with 50MB cap...")

    final_clip.write_videofile(
        output_file,
        fps=24,  # Lower FPS to reduce size
        codec="libx264",
        audio_codec="aac",
        bitrate="500k",  # Enforce max video bitrate
        audio_bitrate="96k",  # Lower audio bitrate
        preset="slow",  # Better compression
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart"
        ]
    )


    os.remove(audio_path)
    if os.path.exists(text_img_path):
        os.remove(text_img_path)

    with open(tracker_path, "w") as f:
        json.dump({
            "last_used_script": script
        }, f, indent=4)

    print(f"✅ Reel saved to: {output_file}")
    if os.path.exists(output_file):
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📊 File size: {size_mb:.2f} MB")

    return output_file, script

if __name__ == "__main__":
    generate_reel()
