import os
import asyncio
import edge_tts
import random
import json
from moviepy.editor import *
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
Image.ANTIALIAS = Image.LANCZOS
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
    # Read the tracker
    try:
        with open(tracker_path, 'r') as f:
            tracker = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        tracker = {"last_used_message": 0}
    
    # Read all messages
    with open(comments_path, "r") as f:
        content = f.read()
    
    # Split by numbered messages
    messages = []
    current_message = []
    current_number = None
    
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check if line starts with a number followed by a period
        if line[0].isdigit() and '. ' in line:
            if current_message:
                messages.append((current_number, '\n'.join(current_message)))
            current_number = int(line.split('.')[0])
            current_message = [line.split('. ', 1)[1]]
        else:
            current_message.append(line)
    
    # Add the last message
    if current_message:
        messages.append((current_number, '\n'.join(current_message)))
    
    # Sort messages by number
    messages.sort(key=lambda x: x[0])
    
    # Find the next message after the last used one
    for number, message in messages:
        if number > tracker["last_used_message"]:
            # Update tracker
            tracker["last_used_message"] = number
            with open(tracker_path, 'w') as f:
                json.dump(tracker, f, indent=4)
            return message
    
    # If we've used all messages, start over
    if messages:
        first_message = messages[0]
        tracker["last_used_message"] = first_message[0]
        with open(tracker_path, 'w') as f:
            json.dump(tracker, f, indent=4)
        return first_message[1]
    
    return "No messages available."

def get_random_background():
    backgrounds = [f for f in os.listdir(background_folder) if f.endswith(('.mp4', '.avi', '.mov'))]
    if not backgrounds:
        raise FileNotFoundError("No background videos found in the background folder.")
    return os.path.join(background_folder, random.choice(backgrounds))

def extend_video(clip, target_duration):
    if clip.duration >= target_duration:
        return clip
    
    # Calculate how many times we need to loop the video
    loops = int(target_duration / clip.duration) + 1
    extended_clip = clip.loop(loops)
    
    # Trim to exact target duration
    return extended_clip.subclip(0, target_duration)

def generate_reel():
    # Step 1: Pick the next comment
    comment = get_next_comment()
    print(f"📝 Today's comment: {comment}")

    # Step 2: Generate TTS using Edge TTS
    asyncio.run(generate_tts(comment, audio_path))
    print("🔊 TTS audio saved.")

    # Step 3: Load and prepare video
    video_path = get_random_background()
    clip = VideoFileClip(video_path)
    clip = clip.resize((1080, 1920))
    
    # Get audio duration
    audioclip = AudioFileClip(audio_path)
    duration = audioclip.duration
    
    # Extend video if needed
    clip = extend_video(clip, duration)

    # Step 4: Animate subtitles phrase-by-phrase (3-4 words per phrase)
    words = comment.split()
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