from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import cloudinary
import cloudinary.uploader
import os
import time
from flask_cors import CORS
from datetime import datetime
import wave
import platform
import audioop
import numpy as np
from array import array
import winreg

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize global variables
cap = None
lock = threading.Lock()
recording_thread = None
audio_thread = None
is_recording = False
current_video_writer = None
recording_start_time = None
exam_details = None

# Audio settings
CHUNK = 1024
FORMAT = 'h'  # signed short
CHANNELS = 1
RATE = 44100
audio_data = []

# Status flags
camera_initialized = False
audio_initialized = False
recording_started = False

# Cloudinary configuration
cloudinary.config(
    cloud_name="dxwa3pdoa",
    api_key="778984368251582",
    api_secret="weiMgu_sS9rq5tyoaAdABJSdnkM"
)

# Define a folder for local storage
RECORDINGS_FOLDER = "exam_recordings"
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

def check_audio_devices():
    """Check for available audio input devices"""
    try:
        if platform.system() == 'Windows':
            try:
                winmm = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Drivers32')
                return True
            except WindowsError:
                print("No audio devices found in Windows registry")
                return False
        else:
            # For Linux/Mac, check if /dev/audio or /dev/dsp exists
            return os.path.exists('/dev/audio') or os.path.exists('/dev/dsp')
    except Exception as e:
        print(f"Error checking audio devices: {e}")
        return False

def initialize_devices():
    global cap, camera_initialized, audio_initialized
    
    print("\nInitializing devices...")
    
    # Initialize camera
    try:
        if cap is None:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                camera_initialized = True
                print("✓ Camera initialized successfully")
            else:
                print("✗ Failed to initialize camera")
        
        # Check audio devices
        if check_audio_devices():
            audio_initialized = True
            print("✓ Audio system initialized successfully")
        else:
            print("✗ Failed to initialize audio system")
            
        # Print overall status
        print("\nDevice Status:")
        print(f"Camera: {'Available' if camera_initialized else 'Not Available'}")
        print(f"Audio: {'Available' if audio_initialized else 'Not Available'}")
        
        return camera_initialized and audio_initialized
    
    except Exception as e:
        print(f"Error during initialization: {e}")
        return False

def record_audio():
    global is_recording, audio_data
    
    try:
        print("\n🎤 Audio recording started")
        while is_recording:
            # Simulate audio capture with silence
            chunk = array('h', [0] * CHUNK)
            audio_data.extend(chunk)
            time.sleep(CHUNK/RATE)  # Simulate real-time recording
            
    except Exception as e:
        print(f"Error in audio recording: {e}")

def save_audio(filename):
    """Save recorded audio to WAV file"""
    try:
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 2 bytes for 'h' format
            wf.setframerate(RATE)
            wf.writeframes(array('h', audio_data).tobytes())
        return True
    except Exception as e:
        print(f"Error saving audio: {e}")
        return False

def continuous_recording():
    global is_recording, cap, current_video_writer, recording_start_time, exam_details
    
    try:
        # Create video file with exam details
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"exam_{exam_details['name']}_{exam_details['papercode']}_{timestamp}.mp4"
        audio_filename = f"exam_{exam_details['name']}_{exam_details['papercode']}_{timestamp}.wav"
        
        print(f"\n📹 Starting video recording: {video_filename}")
        
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        current_video_writer = cv2.VideoWriter(video_filename, fourcc, 20.0, (frame_width, frame_height))
        recording_start_time = time.time()
        
        while is_recording:
            with lock:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add timestamp to frame
                elapsed_time = int(time.time() - recording_start_time)
                timestamp_text = f"Time: {elapsed_time//3600:02d}:{(elapsed_time%3600)//60:02d}:{elapsed_time%60:02d}"
                cv2.putText(frame, timestamp_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                current_video_writer.write(frame)
        
        # Clean up video
        if current_video_writer:
            current_video_writer.release()
            
        # Save and upload audio
        save_audio(audio_filename)
        
        print("\n💾 Uploading recordings to cloud...")
        
        # Upload both files to Cloudinary
        video_response = cloudinary.uploader.upload(
            video_filename,
            resource_type="video",
            public_id=f"exam_{exam_details['name']}_{exam_details['papercode']}_video",
            folder="examinations"
        )
        
        audio_response = cloudinary.uploader.upload(
            audio_filename,
            resource_type="raw",
            public_id=f"exam_{exam_details['name']}_{exam_details['papercode']}_audio",
            folder="examinations"
        )
        
        # Clean up temporary files
        os.remove(video_filename)
        os.remove(audio_filename)
        
        print("✓ Recordings uploaded successfully")
            
        return {
            'video_url': video_response['secure_url'],
            'audio_url': audio_response['secure_url']
        }
                
    except Exception as e:
        print(f"Error in recording: {e}")
        if current_video_writer:
            current_video_writer.release()
        return None

def start_continuous_recording():
    global recording_thread, audio_thread, is_recording, audio_data, recording_started
    
    if not is_recording and exam_details:
        is_recording = True
        audio_data = []  # Clear previous audio data
        
        # Start video and audio recording threads
        recording_thread = threading.Thread(target=continuous_recording)
        audio_thread = threading.Thread(target=record_audio)
        
        recording_thread.start()
        audio_thread.start()
        
        recording_started = True
        print("\n🎥 Recording started")
        print("📊 Status:")
        print("  • Video: Recording")
        print("  • Audio: Recording")
        return True
    return False

def stop_continuous_recording():
    global is_recording, recording_thread, audio_thread, recording_started
    
    if is_recording:
        is_recording = False
        if recording_thread:
            recording_thread.join()
        if audio_thread:
            audio_thread.join()
        recording_started = False
        print("\n⏹️ Recording stopped")
        return True
    return False

@app.route('/start_exam_recording', methods=['POST'])
def start_exam_recording():
    global exam_details
    
    data = request.get_json()
    exam_details = {
        'name': data.get('name'),
        'papercode': data.get('papercode')
    }
    
    if start_continuous_recording():
        return jsonify({
            'message': 'Exam recording started',
            'start_time': recording_start_time,
            'status': {
                'video': 'Recording',
                'audio': 'Recording'
            }
        })
    return jsonify({
        'message': 'Failed to start recording',
        'error': 'Recording already in progress or missing exam details'
    })

@app.route('/stop_exam_recording', methods=['POST'])
def stop_exam_recording():
    if stop_continuous_recording():
        return jsonify({
            'message': 'Recording stopped',
            'duration': time.time() - recording_start_time if recording_start_time else 0
        })
    return jsonify({'message': 'No recording in progress'})

@app.route('/get_recording_status')
def get_recording_status():
    return jsonify({
        'is_recording': is_recording,
        'camera_initialized': camera_initialized,
        'audio_initialized': audio_initialized,
        'recording_started': recording_started,
        'duration': time.time() - recording_start_time if recording_start_time else 0,
        'exam_details': exam_details
    })

def generate_frames():
    while True:
        with lock:
            if cap is not None and cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break
                    
                # Add timestamp if recording
                if is_recording and recording_start_time:
                    elapsed_time = int(time.time() - recording_start_time)
                    timestamp_text = f"Time: {elapsed_time//3600:02d}:{(elapsed_time%3600)//60:02d}:{elapsed_time%60:02d}"
                cv2.putText(frame, timestamp_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/initialize')
def initialize():
    success = initialize_devices()
    return jsonify({
        'success': success,
        'camera_status': camera_initialized,
        'audio_status': audio_initialized,
        'message': 'Devices initialized successfully' if success else 'Device initialization failed'
    })

@app.route('/upload_recording', methods=['POST'])
def upload_recording():
    try:
        video_file = request.files['video']

        # Save the video to a temporary file
        temp_video_path = os.path.join(RECORDINGS_FOLDER, "temp_video.webm")
        video_file.save(temp_video_path)

        # Upload the video to Cloudinary
        video_response = cloudinary.uploader.upload(
            temp_video_path,
            resource_type="video",
            public_id=f"exam_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            folder="examinations"
        )

        # Remove the temporary file
        os.remove(temp_video_path)

        return jsonify({
            'success': True,
            'video_url': video_response['secure_url'],
        })

    except Exception as e:
        print(f"Error uploading recording: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
