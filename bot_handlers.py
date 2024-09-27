import os
import tempfile
from telegram import Update
from telegram.ext import CallbackContext
from moviepy.editor import ImageSequenceClip, AudioFileClip, CompositeVideoClip
import requests
from io import BytesIO
from PIL import Image
import numpy as np

from config import sp
from image_processing import create_circular_image, rotate_image
from spotify_handler import get_track_info

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я могу сделать тебе кружочек, нужно лишь отправить ссылку на трек со Spotify')

def handle_spotify_link(update: Update, context: CallbackContext) -> None:
    message = update.message
    spotify_url = message.text

    try:
        track_info = get_track_info(spotify_url)

        if track_info['album']['images'] and track_info['preview_url']:
            message.reply_text("Генерирую твой кружочек...")

            # Download album cover
            image_url = track_info['album']['images'][0]['url']
            image_response = requests.get(image_url)
            image = Image.open(BytesIO(image_response.content))

            # Create circular image
            size = 480
            circular_image = create_circular_image(image, size)

            # Create rotating frames
            frames = []
            fps = 30
            duration = 20
            total_frames = fps * duration
            for i in range(total_frames):
                angle = i * (-360 / total_frames)
                rotated = rotate_image(circular_image, angle)
                frames.append(np.array(rotated))

            rotating_clip = ImageSequenceClip(frames, fps=fps)

            # Download and process audio
            audio_url = track_info['preview_url']
            audio_response = requests.get(audio_url)

            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio_file:
                temp_audio_file.write(audio_response.content)
                temp_audio_path = temp_audio_file.name

            audio_clip = AudioFileClip(temp_audio_path)
            audio_clip = audio_clip.subclip(0, min(20, audio_clip.duration))

            video = CompositeVideoClip([rotating_clip]).set_audio(audio_clip)

            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video_file:
                temp_video_path = temp_video_file.name

            video.write_videofile(temp_video_path, codec='libx264', audio_codec='aac',
                                  fps=fps, bitrate="800k",
                                  ffmpeg_params=["-crf", "23", "-preset", "faster"],
                                  temp_audiofile=None, remove_temp=True, write_logfile=False)
            video.close()

            with open(temp_video_path, 'rb') as video_file:
                message.reply_video_note(video_file)

            os.unlink(temp_audio_path)
            os.unlink(temp_video_path)

        else:
            message.reply_text("У этого трека нет обложки альбома или аудиопревью, попробуй отправить мне другой трек!")
    except Exception as e:
        message.reply_text(f"Возникла ошибка: {str(e)}")