import os
import asyncio
import edge_tts
import random
import re
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import json
import numpy as np

# Paths
base_path = os.path.dirname(os.path.abspath(__file__))
quiz_path = os.path.join(base_path, "cricket_quiz.txt")
tracker_path = os.path.join(base_path, "quiz_tracker.json")
background_folder = os.path.join(base_path, "background")
output_path = os.path.join(base_path, "output")
audio_intro_path = os.path.join(base_path, "audio_intro.mp3")
audio_question_path = os.path.join(base_path, "audio_question.mp3")
audio_answer_path = os.path.join(base_path, "audio_answer.mp3")
font_path = os.path.join(base_path, "fonts", "Montserrat-Bold.ttf")

# Helper for temporary text images
TEMP_TEXT_IMAGES = []

def get_day_intro(quiz_number):
    return f"Day {quiz_number} of 50 days 50 interesting cricket questions."

async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
    await communicate.save(output_file)

def create_text_image(text, size=(1000, 200), max_font_size=80):
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
    # Save to a unique temp file
    temp_img_path = os.path.join(base_path, f"text_overlay_{random.randint(0, 1e9)}.png")
    img.save(temp_img_path)
    TEMP_TEXT_IMAGES.append(temp_img_path)
    return temp_img_path

def get_next_quiz():
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
    try:
        with open(tracker_path, "r") as f:
            tracker = json.load(f)
            last_used = tracker.get("last_used_question", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        last_used = 0
    for number, question, answer in sorted(quizzes):
        if number > last_used:
            return number, question, answer
    return None, "All questions have been used.", ""

def get_random_background():
    videos = [f for f in os.listdir(background_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not videos:
        raise FileNotFoundError("No background videos found.")
    return os.path.join(background_folder, random.choice(videos))

def loop_background(clip, duration_needed):
    if clip.duration >= duration_needed:
        return clip.subclip(0, duration_needed)
    loops = int(duration_needed // clip.duration) + 1
    looped = concatenate_videoclips([clip] * loops)
    return looped.subclip(0, duration_needed)

def make_silence(duration, fps=44100):
    return AudioClip(lambda t: np.zeros((len(np.atleast_1d(t)), 2)), duration=duration, fps=fps)

def make_subtitle_clips(text, start_time, duration, size=(1000, 200), max_font_size=80):
    words = text.split()
    phrases = [' '.join(words[i:i + 3]) for i in range(0, len(words), 3)]
    phrase_duration = duration / len(phrases)
    clips = []
    for i, phrase in enumerate(phrases):
        img = create_text_image(phrase, size=size, max_font_size=max_font_size)
        txt_clip = (ImageClip(img)
                    .set_duration(phrase_duration)
                    .set_start(start_time + i * phrase_duration)
                    .set_position("center"))  # Center both vertically and horizontally
        clips.append(txt_clip)
    return clips

def generate_quiz_reel():
    quiz_number, question, answer = get_next_quiz()
    if quiz_number is None:
        print("🚫 All questions have been used.")
        return
    print(f"📝 Generating quiz reel for question #{quiz_number}: {question}")
    # Day intro
    day_intro = get_day_intro(quiz_number)
    asyncio.run(generate_tts(day_intro, audio_intro_path))
    audioclip_intro = AudioFileClip(audio_intro_path)
    duration_intro = audioclip_intro.duration
    img_intro = create_text_image(day_intro)
    txt_clip_intro = (ImageClip(img_intro)
                      .set_duration(duration_intro)
                      .set_start(0)
                      .set_position("center"))
    # TTS for question
    asyncio.run(generate_tts(question, audio_question_path))
    audioclip_q = AudioFileClip(audio_question_path)
    duration_q = audioclip_q.duration
    # Subtitle overlays for question
    subtitle_clips_q = make_subtitle_clips(question, duration_intro, duration_q)
    # 5 second pause with overlay
    pause_text = "Comment your answer below"
    img_pause = create_text_image(pause_text)
    pause_clip = (ImageClip(img_pause)
                  .set_duration(5)
                  .set_start(duration_intro + duration_q)
                  .set_position("center"))
    pause_audio = make_silence(5)
    # TTS for answer
    asyncio.run(generate_tts(answer, audio_answer_path))
    audioclip_a = AudioFileClip(audio_answer_path)
    duration_a = audioclip_a.duration
    # Subtitle overlays for answer
    subtitle_clips_a = make_subtitle_clips(answer, duration_intro + duration_q + 5, duration_a)
    video_path = get_random_background()
    total_duration = duration_intro + duration_q + 5 + duration_a
    clip = VideoFileClip(video_path).resize((1080, 1920))
    clip = loop_background(clip, total_duration)
    # Audio composition
    final_audio = concatenate_audioclips([
        audioclip_intro,
        audioclip_q,
        pause_audio,
        audioclip_a
    ])
    # Video composition
    final_clip = CompositeVideoClip([
        clip,
        txt_clip_intro,
        pause_clip,
        *subtitle_clips_q,
        *subtitle_clips_a
    ]).set_audio(final_audio)
    filename = f"quiz_reel_{quiz_number}.mp4"
    output_file = os.path.join(output_path, filename)
    print("🎬 Encoding quiz video for Instagram...")
    final_clip.write_videofile(
        output_file,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
        preset="medium",
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",
            "-crf", "23",
            "-maxrate", "8000k",
            "-bufsize", "12000k",
            "-movflags", "+faststart"
        ]
    )
    # Clean up all temp audio and text images
    for f in [audio_intro_path, audio_question_path, audio_answer_path]:
        if os.path.exists(f):
            os.remove(f)
    for img in TEMP_TEXT_IMAGES:
        if os.path.exists(img):
            os.remove(img)
    print(f"✅ Quiz reel saved to: {output_file}")
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"📊 File size: {file_size:.2f} MB")
        if file_size < 0.1:
            print("⚠️ Warning: File size seems too small")
        elif file_size > 100:
            print("⚠️ Warning: File size seems too large for Instagram")
    with open(tracker_path, "w") as f:
        json.dump({
            "last_used_question": quiz_number,
            "last_used_text": question
        }, f, indent=4)
    return output_file, question

if __name__ == "__main__":
    generate_quiz_reel() 