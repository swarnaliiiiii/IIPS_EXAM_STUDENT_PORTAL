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
    const [streamUrl, setStreamUrl] = useState(null);

    useEffect(() => {
        if (!loginStatus) {
            stopTest();
        }
    }, [loginStatus]);

    useEffect(() => {
        if (verified) {
            navigate("/rules");
        }
    }, [verified, navigate]);
   useEffect(() => {
        const getPermissions = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: true,
                    audio: true
                });
                /* use the stream */
                 setDeviceStatus(prevState => ({
                    ...prevState,
                    camera: true,
                    audio: true,
                    checking: false
                }));
                   setStreamUrl("http://127.0.0.1:5000/video_feed")
                setTestStatus('Devices are ready! Please Wait ...');
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
            } catch (err) {
                /* handle the error */
                 setDeviceStatus(prevState => ({
                    ...prevState,
                    camera: false,
                    audio: false,
                    checking: false
                }));
                setTestStatus(`Failed to access devices: ${err.message}. Please check permissions.`);
                console.error("Failed to access devices:", err);
            }
        }
        getPermissions();
    }, []);
    const checkDevices = () => {
           setDeviceStatus(prevState => ({
                ...prevState,
                checking: true
            }));
        setTestStatus("Checking the devices...");
        fetch('http://127.0.0.1:5000/initialize')
            .then((response) => response.json())
            .then((data) => {
                setDeviceStatus({
                    camera: data.camera_status,
                    audio: data.audio_status,
                    checking: false
                });
                  if (data.camera_status ) {
                    setTestStatus('Devices are ready! Please Wait ...');
                    setStreamUrl("http://127.0.0.1:5000/video_feed")
                } else {
                    setTestStatus('Some devices are not ready. Please check your camera. Press f12 to look into the camera error');
                }
            })
            .catch((error) => {
                console.error('Error checking devices:', error);
                setTestStatus('Error checking devices. Please refresh the page.');
                setDeviceStatus(prev => ({ ...prev, checking: false }));
            });
    };

    const startTest = () => {
        if (!deviceStatus.camera) {
            alert('Please ensure your camera is working before starting the test.');
            return;
        }

        setIsRecording(true);
        setTestStatus('Please wait...');

        fetch('http://127.0.0.1:5000/start_exam_recording', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                papercode
            })
        })
            .then(() => {
                const intervalId = setInterval(() => {
                    fetch('http://127.0.0.1:5000/get_recording_status')
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
        fetch('http://127.0.0.1:5000/stop_exam_recording', {
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
                    <li>Camera Status: {deviceStatus.camera ? '✅ Ready' : '⏳ Checking...' + (deviceStatus.checking ? "Checking devices..." : "")}</li>
                    <li>Microphone Status: {deviceStatus.audio ? '✅ Ready' : '⏳ Checking...' + (deviceStatus.checking ? "Checking devices..." : "")}</li>
                    <li>Once both devices are ready, you can start the test</li>
                </ul>
            </div>

            <h3 className="verification_webcam_heading">Webcam Feed</h3>
            {streamUrl ? (
                <img
                    id="verification_webcam"
                    className="verification_webcam"
                    src={streamUrl}
                    alt="Webcam feed"
                />
            ) : (
                <p>Webcam feed will appear here after initialization.</p>
            )}
            {!deviceStatus.checking && deviceStatus.camera && (
                <button
                    className="verification_start_test_btn"
                    onClick={startTest}
                    disabled={isRecording}
                >
                    {isRecording ? 'Please Wait...' : 'Start Test'}
                </button>
            )}
            {!deviceStatus.checking ? (
                !deviceStatus.camera && (
                    <button
                        className="verification_start_test_btn"
                        onClick={checkDevices}
                    >
                        Retry Device Check
                    </button>
                )
            ) : (
                <button
                    className="verification_start_test_btn"
                    onClick={checkDevices}
                >
                    Checking Devices
                </button>
            )}
            <div className="verification_test_status">
                Status: {testStatus}
            </div>
        </div>
    );
};

export default Verification;
