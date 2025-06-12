import os
import asyncio
import edge_tts
import random
from moviepy.editor import *
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# Paths
base_path = os.path.dirname(os.path.abspath(__file__))
comments_path = os.path.join(base_path, "cricket_comments.txt")
background_folder = os.path.join(base_path, "background")
output_path = os.path.join(base_path, "output")
audio_path = os.path.join(base_path, "audio.mp3")
text_img_path = os.path.join(base_path, "text_overlay.png")
font_path = os.path.join(base_path, "fonts", "Montserrat-Bold.ttf")

async def generate_tts(text, output_file):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural")
    await communicate.save(output_file)

def create_text_image(text, size=(900, 300), font_size=100):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    w, h = draw.multiline_textsize(text, font=font)
    x = (size[0] - w) // 2
    y = (size[1] - h) // 2
    draw.multiline_text((x, y), text, font=font, fill="white", align="center")
    img.save(text_img_path)
    return text_img_path

def get_next_comment():
    with open(comments_path, "r") as f:
        comments = [line.strip() for line in f if line.strip()]
    if not comments:
        return "No comments available."
    for i, comment in enumerate(comments):
        if not comment.startswith('#'):
            comments[i] = '#' + comment
            with open(comments_path, "w") as f:
                f.write("\n".join(comments))
            return comment
    return "All comments have been used."

def get_random_background():
    backgrounds = [f for f in os.listdir(background_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not backgrounds:
        raise FileNotFoundError("No background videos found in the background folder.")
    return os.path.join(background_folder, random.choice(backgrounds))

def generate_reel():
    # Step 1: Pick the next comment line-by-line
    comment = get_next_comment()
    print(f"📝 Today's comment: {comment}")

    # Step 2: Generate TTS using Edge TTS
    asyncio.run(generate_tts(comment, audio_path))
    print("🔊 TTS audio saved.")

    # Step 3: Load and trim video (30 seconds max)
    video_path = get_random_background()
    clip = VideoFileClip(video_path)
    if clip.duration > 30:
        start_time = random.uniform(0, clip.duration - 30)
        clip = clip.subclip(start_time, start_time + 30)
    clip = clip.resize((1080, 1920))

    # Step 4: Animate subtitles phrase-by-phrase (3-4 words per phrase)
    words = comment.split()
    audioclip = AudioFileClip(audio_path)
    duration = audioclip.duration
    phrase_size = 3  # Number of words per phrase
    phrases = [' '.join(words[i:i + phrase_size]) for i in range(0, len(words), phrase_size)]
    phrase_duration = duration / len(phrases)
    text_clips = []
    for i, phrase in enumerate(phrases):
        start_time = i * phrase_duration
        end_time = (i + 1) * phrase_duration
        text_img = create_text_image(phrase, size=(900, 300), font_size=100)
        txt_clip = (ImageClip(text_img)
                    .set_duration(end_time - start_time)
                    .set_start(start_time)
                    .set_position(("center", "center")))
        text_clips.append(txt_clip)

    # Step 5: Add audio and export
    final_clip = CompositeVideoClip([clip] + text_clips)
    final_clip = final_clip.set_audio(audioclip)

    # Step 6: Export
    filename = f"reel_{datetime.now().strftime('%Y%m%d')}.mp4"
    final_file = os.path.join(output_path, filename)
    final_clip.write_videofile(final_file, fps=24, codec="libx264", audio_codec="aac")

    # Cleanup temporary files
    os.remove(audio_path)
    if os.path.exists(text_img_path):
        os.remove(text_img_path)
    
    print(f"✅ Reel generated: {final_file}")
    return final_file

if __name__ == "__main__":
    generate_reel() 