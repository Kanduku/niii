from flask import Flask, request, jsonify, send_from_directory
import os
from pytube import YouTube
import moviepy.editor as mp
import librosa
import numpy as np
import cv2
import time
import subprocess
import sys

app = Flask(__name__)

# Directory where the generated videos will be stored
GENERATED_VIDEO_DIR = './generated_videos'
if not os.path.exists(GENERATED_VIDEO_DIR):
    os.makedirs(GENERATED_VIDEO_DIR)

# Function to install MoviePy, librosa, and numpy
def install_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "moviepy==1.0.3", "librosa==0.10.0", "numpy==1.26.4", "opencv-python==4.10.0.84"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

# Install dependencies if not already installed
try:
    import moviepy.editor as mp
    import librosa
    import numpy as np
except ImportError:
    install_dependencies()

@app.route('/generate-video', methods=['POST'])
def generate_video():
    # Receive YouTube URL from the frontend
    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Download the YouTube video
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        audio_path = os.path.join(GENERATED_VIDEO_DIR, f"{yt.title}.mp4")
        stream.download(output_path=GENERATED_VIDEO_DIR, filename=f"{yt.title}.mp4")

        # Extract audio from the video
        audio_clip = mp.AudioFileClip(audio_path)
        audio_path_mp3 = os.path.join(GENERATED_VIDEO_DIR, f"{yt.title}.mp3")
        audio_clip.write_audiofile(audio_path_mp3)

        # Analyze audio to generate video (simple random motion)
        video_path = os.path.join(GENERATED_VIDEO_DIR, f"{yt.title}_motion_video.mp4")
        frame_rate = 30
        width, height = 640, 480
        out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), frame_rate, (width, height))

        for i in range(100):  # Creating 100 frames as an example
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :, 0] = np.random.randint(0, 255, (height, width), dtype=np.uint8)  # Random colors
            out.write(frame)

        out.release()

        # Return the generated video URL for downloading
        return jsonify({"message": "Video generated successfully", "video_url": f"/download/{yt.title}_motion_video.mp4"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>', methods=['GET'])
def download_video(filename):
    try:
        return send_from_directory(GENERATED_VIDEO_DIR, filename)
    except Exception as e:
        return jsonify({"error": f"File not found: {filename}"}), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
