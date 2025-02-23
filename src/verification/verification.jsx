import React, { useState, useEffect } from 'react';
import "./verification.css";
import { useNavigate } from 'react-router-dom';

const Verification = () => {
  const [deviceStatus, setDeviceStatus] = useState({
    camera: false,
    audio: false,
    checking: true
  });
  const [testStatus, setTestStatus] = useState('Checking devices...');
  const [isRecording, setIsRecording] = useState(false);
  const loginStatus = localStorage.getItem('loginStatus') === 'true'; // Ensure it's a boolean
  const name = localStorage.getItem('name');
  const verified = localStorage.getItem("verified");
  const papercode = localStorage.getItem('papercode');
  const navigate = useNavigate();

  useEffect(() => {
    checkDevices();
    if (!loginStatus) {
      stopTest();
    }
  }, [loginStatus]);

  useEffect(() => {
    if (verified) {
      navigate("/rules");
    }
  }, [verified, navigate]);

  const checkDevices = () => {
    fetch('http://127.0.0.1:5000/initialize') // Updated endpoint
      .then((response) => response.json())
      .then((data) => {
        setDeviceStatus({
          camera: data.camera_status, // Adjusted according to Flask response
          audio: data.audio_status,
          checking: false
        });

        if (data.camera_status && data.audio_status) {
          setTestStatus('Devices are ready! Please Wait ...');
        } else {
          setTestStatus('Some devices are not ready. Please check your camera and microphone permissions.');
        }
      })
      .catch((error) => {
        console.error('Error checking devices:', error);
        setTestStatus('Error checking devices. Please refresh the page.');
        setDeviceStatus(prev => ({ ...prev, checking: false }));
      });
  };

  const startTest = () => {
    if (!deviceStatus.camera || !deviceStatus.audio) {
      alert('Please ensure both camera and microphone are working before starting the test.');
      return;
    }

    setIsRecording(true);
    setTestStatus('Please wait...');

    fetch('http://127.0.0.1:5000/start_exam_recording', { // Updated endpoint
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        name, 
        papercode 
      })
    })
      .then(() => {
        const intervalId = setInterval(() => {
          fetch('http://127.0.0.1:5000/get_recording_status') // Updated endpoint
            .then((response) => response.json())
            .then((statusData) => {
              if (statusData.is_recording) {
                setTestStatus('Recording in progress... Please wait...');
              } else if (statusData.recording_started) {
                setTestStatus('Recording completed! You can now proceed with the test.');
                setIsRecording(false);
                clearInterval(intervalId);
                localStorage.setItem("verified", true);
                navigate('/rules');
              }
            });
        }, 1000);
      })
      .catch((error) => {
        console.error(error);
        setIsRecording(false);
        setTestStatus('Error in recording. Please try again.');
      });
  };

  const stopTest = () => {
    setIsRecording(false);
    setTestStatus('Recording stopped due to logout.');
    
    // Send a request to stop the recording on the server
    fetch('http://127.0.0.1:5000/stop_exam_recording', { // Updated endpoint
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        name, 
        papercode 
      })
    });
  };

  return (
    <div className="verification_container">
      <div className="verification_instructions">
        <h2 className="verification_instructions_heading">Instructions:</h2>
        <p className="verification_instructions_text">
          System will check your devices and prepare for the test:
        </p>
        <ul className="verification_instructions_list">
          <li>Camera Status: {deviceStatus.camera ? '✅ Ready' : '⏳ Checking...'}</li>
          <li>Microphone Status: {deviceStatus.audio ? '✅ Ready' : '⏳ Checking...'}</li>
          <li>Once both devices are ready, you can start the test</li>
        </ul>
      </div>

      <h3 className="verification_webcam_heading">Webcam Feed</h3>
      <img
        id="verification_webcam"
        className="verification_webcam"
        src="http://127.0.0.1:5000/video_feed"
        alt="Webcam feed"
      />

      {!deviceStatus.checking && deviceStatus.camera && deviceStatus.audio && (
        <button 
          className="verification_start_test_btn"
          onClick={startTest}
          disabled={isRecording}
        >
          {isRecording ? 'Please Wait...' : 'Start Test'}
        </button>
      )}

      {!deviceStatus.checking && (!deviceStatus.camera || !deviceStatus.audio) && (
        <button 
          className="verification_start_test_btn"
          onClick={checkDevices}
        >
          Retry Device Check
        </button>
      )}

      <div className="verification_test_status">
        Status: {testStatus}
      </div>
    </div>
  );
};

export default Verification;
