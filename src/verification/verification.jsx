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
  const loginStatus  = useState(localStorage?.getItem('loginStatus'));
  const name = localStorage.getItem('name');
  const verified=localStorage.getItem("verified");
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
  }, [])

  const checkDevices = () => {
    fetch('https://iips-exam-student-portal.onrender.com/initialize_devices')
      .then((response) => response.json())
      .then((data) => {
        setDeviceStatus({
          camera: data.camera_ready,
          audio: data.audio_ready,
          checking: false
        });
        
        if (data.camera_ready && data.audio_ready) {
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

    fetch('https://iips-exam-student-portal.onrender.com/start_test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        name, 
        papercode, 
        login_status: loginStatus  // Send login status to the server
      })
    })
      .then(() => {
        const intervalId = setInterval(() => {
          fetch('https://iips-exam-student-portal.onrender.com/check_test_status')
            .then((response) => response.json())
            .then((statusData) => {
              if (statusData.recording_in_progress) {
                setTestStatus(' Please wait.....');
              } else if (statusData.test_ready) {
                setTestStatus('Recording completed! You can now proceed with the test.');
                setIsRecording(false);
                clearInterval(intervalId);
                localStorage.setItem("verified",true);
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
    fetch('https://iips-exam-student-portal.onrender.com/start_test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        name, 
        papercode, 
        login_status: false // Stop recording by setting login_status to false
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
        src="https://iips-exam-student-portal.onrender.com/video_feed"
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
