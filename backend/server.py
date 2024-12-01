from flask import Flask, render_template, Response, jsonify, request
import cv2
from mtcnn.mtcnn import MTCNN
from pydub import AudioSegment
import subprocess  # For calling ffmpeg directly
import wave
import threading
import cloudinary
import cloudinary.uploader
import os
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
port = int(os.environ.get("PORT", 8000))  # Render uses dynamic ports

# Initialize global variables
cap = None
detector = MTCNN()
lock = threading.Lock()

# Status flags
camera_ready = False
recording_in_progress = False
test_ready = False

# Cloudinary configuration using environment variables for security
cloudinary.config(
    cloud_name="duxvbwdf3",
    api_key="282754191399316",
    api_secret="4NYTt_3v2JK7-O0KUN9UwKrAWiE"
)

def initialize_devices():
    global cap, camera_ready
    
    try:
        # Initialize camera
        print("Camera initialized successfully")
        if cap is None:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                camera_ready = True
                print("Camera initialized successfully")
            else:
                print("Failed to initialize camera")
                return False
        
        return camera_ready
    
    except Exception as e:
        print(f"Error initializing devices: {e}")
        return False

def record_audio_with_ffmpeg(name, papercode, duration=5):
    try:
        file_basename = f"{name}_{papercode}"
        filename = f"{file_basename}_audio.wav"
        
        # Use ffmpeg to record audio from the default system microphone
        subprocess.run([
            "ffmpeg", "-y", "-f", "alsa", "-i", "default",
            "-t", str(duration), filename
        ])
        
        # Upload to Cloudinary
        response = cloudinary.uploader.upload(
            filename,
            resource_type="raw",
            public_id=f"{file_basename}_audio",
            folder="media"
        )
        
        # Clean up temporary file
        if os.path.exists(filename):
            os.remove(filename)
        
        return response['secure_url']
    
    except Exception as e:
        print(f"Error recording audio: {e}")
        return None

def record_video(name, papercode, duration=5):
    global recording_in_progress
    
    try:
        recording_in_progress = True
        file_basename = f"{name}_{papercode}"
        temp_filename = f"{file_basename}_video.mp4"
        
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(temp_filename, fourcc, 20.0, (frame_width, frame_height))
        
        start_time = time.time()
        while time.time() - start_time < duration:
            with lock:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Detect faces in the frame using MTCNN
                faces = detector.detect_faces(frame)
                
                # Draw a box around each detected face
                for face in faces:
                    x, y, width, height = face['box']
                    x2, y2 = x + width, y + height
                    cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)
                
                out.write(frame)
                    
        out.release()
        
        # Upload to Cloudinary
        response = cloudinary.uploader.upload(
            temp_filename,
            resource_type="video",
            public_id=f"{file_basename}_video",
            folder="media"
        )
        
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
        recording_in_progress = False
        return response['secure_url']
    
    except Exception as e:
        print(f"Error recording video: {e}")
        recording_in_progress = False
        return None

def run_test_recording(name, papercode, login_status):
    global test_ready
    try:
        while login_status:  # Keep recording until the login status is false
            video_url = record_video(name, papercode)
            audio_url = record_audio_with_ffmpeg(name, papercode)
            
            if video_url and audio_url:
                test_ready = True
                return {'status': 'success', 'video_url': video_url, 'audio_url': audio_url}
            else:
                return {'status': 'error', 'message': 'Failed to record video or audio'}
            
        return {'status': 'error', 'message': 'Recording stopped due to logout'}
            
    except Exception as e:
        print(f"Error during recording: {e}")
        return {'status': 'error', 'message': str(e)}

@app.route('/start_test', methods=['POST'])
def start_test():
    global test_ready
    test_ready = False
    
    data = request.get_json()
    name = data.get('name')
    papercode = data.get('papercode')
    login_status = data.get('login_status')  # Retrieve login status
    
    test_thread = threading.Thread(target=run_test_recording, args=(name, papercode, login_status))
    test_thread.start()
    
    return jsonify({'message': 'Recording started'})

@app.route('/check_test_status')
def check_test_status():
    return jsonify({
        'camera_ready': camera_ready,
        'recording_in_progress': recording_in_progress,
        'test_ready': test_ready
    })

@app.route('/initialize_devices')
def check_devices():
    success = initialize_devices()
    return jsonify({
        'success': success,
        'camera_ready': camera_ready
    })

def generate_frames():
    while True:
        with lock:
            if cap is not None and cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
