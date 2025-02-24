from flask import Flask, jsonify, request
import cloudinary
import cloudinary.uploader
import os
from flask_cors import CORS
from datetime import datetime
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Status flags
recording_started = False
exam_details = None

# Cloudinary configuration
cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', 'dxwa3pdoa'),
    api_key=os.getenv('CLOUDINARY_API_KEY', '778984368251582'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET', 'weiMgu_sS9rq5tyoaAdABJSdnkM')
)

RECORDINGS_FOLDER = "exam_recordings"
if not os.path.exists(RECORDINGS_FOLDER):
    os.makedirs(RECORDINGS_FOLDER)

@app.route('/initialize')
def initialize():
    return jsonify({
        'success': True,
        'camera_status': True,
        'audio_status': True,
        'message': 'Client-side devices can be initialized'
    })

@app.route('/start_exam_recording', methods=['POST'])
def start_exam_recording():
    global exam_details, recording_started
    
    data = request.get_json()
    exam_details = {
        'name': data.get('name'),
        'papercode': data.get('papercode')
    }
    recording_started = True
    
    return jsonify({
        'message': 'Exam recording can be started',
        'status': 'Recording'
    })

@app.route('/upload_video_chunk', methods=['POST'])
def upload_video_chunk():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
        
    video_file = request.files['video']
    name = request.form.get('name')
    papercode = request.form.get('papercode')
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exam_{name}_{papercode}_{timestamp}.webm"
        filepath = os.path.join(RECORDINGS_FOLDER, filename)
        
        # Save file temporarily
        video_file.save(filepath)
        
        # Upload to Cloudinary
        response = cloudinary.uploader.upload(
            filepath,
            resource_type="video",
            public_id=f"exam_{name}_{papercode}_video",
            folder="examinations"
        )
        
        # Clean up local file
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'url': response['secure_url']
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/get_recording_status')
def get_recording_status():
    return jsonify({
        'is_recording': recording_started,
        'recording_started': recording_started,
        'exam_details': exam_details
    })

if __name__ == '__main__':
    app.run(debug=True)