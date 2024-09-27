import os
import tempfile
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip
import requests
from io import BytesIO
from PIL import Image, ImageDraw
import numpy as np

load_dotenv()  # Load environment variables

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Initialize Spotify client
sp = Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                                   client_secret=SPOTIFY_CLIENT_SECRET))

def create_circular_image(image, size):
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)

    output = image.copy()
    output = output.resize((size, size), Image.LANCZOS)
    output.putalpha(mask)

    background = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    background.paste(output, (0, 0), output)
    return background

def rotate_image(image, angle):
    return image.rotate(angle, resample=Image.BICUBIC, expand=False)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я могу сделать тебе кружочек, нужно лишь отправить ссылку на трек со Spotify')

def handle_spotify_link(update: Update, context: CallbackContext) -> None:
    message = update.message
    spotify_url = message.text

    try:
        # Get track information
        track_id = spotify_url.split('/')[-1].split('?')[0]
        track_info = sp.track(track_id)

        # Check if album cover and preview are available
        if track_info['album']['images'] and track_info['preview_url']:
            message.reply_text("Генерирую твой кружочек...")
            # Download album cover
            image_url = track_info['album']['images'][0]['url']
            image_response = requests.get(image_url)
            image = Image.open(BytesIO(image_response.content))

            # Create circular image
            size = 480  # Increased size for better quality
            circular_image = create_circular_image(image, size)

            # Create rotating frames
            frames = []
            fps = 30  # Higher FPS for smoother rotation
            duration = 20  # 20 seconds video
            total_frames = fps * duration
            for i in range(total_frames):
                angle = i * (-360 / total_frames)  # Smooth rotation over 20 seconds
                rotated = rotate_image(circular_image, angle)
                frames.append(np.array(rotated))

            rotating_clip = ImageSequenceClip(frames, fps=fps)

            # Download and process audio
            audio_url = track_info['preview_url']
            audio_response = requests.get(audio_url)

            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio_file:
                temp_audio_file.write(audio_response.content)
                temp_audio_path = temp_audio_file.name

            audio_clip = AudioFileClip(temp_audio_path)
            audio_clip = audio_clip.subclip(0, min(20, audio_clip.duration))

            video = CompositeVideoClip([rotating_clip]).set_audio(audio_clip)

            # Create a temporary file for the video
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video_file:
                temp_video_path = temp_video_file.name

            # Write video to the temporary file
            video.write_videofile(temp_video_path, codec='libx264', audio_codec='aac',
                                  fps=fps, bitrate="800k",
                                  ffmpeg_params=["-crf", "23", "-preset", "faster"],
                                  temp_audiofile=None, remove_temp=True, write_logfile=False)
            video.close()

            # Send video note
            with open(temp_video_path, 'rb') as video_file:
                message.reply_video_note(video_file)

            # Remove the temporary files
            os.unlink(temp_audio_path)
            os.unlink(temp_video_path)

        else:
            message.reply_text("У этого трека нет обложки альбома или аудиопревью, попробуй отправить мне другой трек!")
    except Exception as e:
        message.reply_text(f"Возникла ошибка: {str(e)}")

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_spotify_link))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()