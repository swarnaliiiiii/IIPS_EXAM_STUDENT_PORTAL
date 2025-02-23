from flask import Flask, render_template, Response, jsonify, request
import cv2
import threading
import cloudinary
import cloudinary.uploader
import os
import time
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize global variables
cap = None
lock = threading.Lock()
recording_thread = None
is_recording = False
current_video_writer = None
recording_start_time = None
exam_details = None

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
        
        audio_initialized = True  # Assume audio is initialized
        print("✓ Audio system assumed to be initialized successfully")
        # Print overall status
        print("\nDevice Status:")
        print(f"Camera: {'Available' if camera_initialized else 'Not Available'}")
        print(f"Audio: {'Available' if audio_initialized else 'Always Available'}") # Added always available
        
        return camera_initialized 
    
    except Exception as e:
        print(f"Error during initialization: {e}")
        return False


def continuous_recording():
    global is_recording, cap, current_video_writer, recording_start_time, exam_details
    
    try:
        # Create video file with exam details
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_filename = f"exam_{exam_details['name']}_{exam_details['papercode']}_{timestamp}.mp4"
        
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
            
        print("\n💾 Uploading recordings to cloud...")
        
        # Upload both files to Cloudinary
        video_response = cloudinary.uploader.upload(
            video_filename,
            resource_type="video",
            public_id=f"exam_{exam_details['name']}_{exam_details['papercode']}_video",
            folder="examinations"
        )
        
        # Clean up temporary files
        os.remove(video_filename)
        
        print("✓ Recordings uploaded successfully")
            
        return {
            'video_url': video_response['secure_url'],
        }
                
    except Exception as e:
        print(f"Error in recording: {e}")
        if current_video_writer:
            current_video_writer.release()
        return None

def start_continuous_recording():
    global recording_thread, is_recording, recording_started
    
    if not is_recording and exam_details:
        is_recording = True
        
        # Start video and audio recording threads
        recording_thread = threading.Thread(target=continuous_recording)
        
        recording_thread.start()
        
        recording_started = True
        print("\n🎥 Recording started")
        print("📊 Status:")
        print("  • Video: Recording")
        return True
    return False

def stop_continuous_recording():
    global is_recording, recording_thread, recording_started
    
    if is_recording:
        is_recording = False
        if recording_thread:
            recording_thread.join()
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
        'audio_status': True,
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
