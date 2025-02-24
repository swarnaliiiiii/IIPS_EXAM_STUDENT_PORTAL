import React, { useState, useEffect, useRef } from 'react';
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
    const loginStatus = localStorage.getItem('loginStatus') === 'true';
    const name = localStorage.getItem('name');
    const verified = localStorage.getItem("verified");
    const papercode = localStorage.getItem('papercode');
    const navigate = useNavigate();
    const videoRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const streamRef = useRef(null);
    const backendUrl = "https://backend-o9s5.onrender.com";
    const chunksRef = useRef([]);

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
                
                streamRef.current = stream;
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
                
                setDeviceStatus(prevState => ({
                    ...prevState,
                    camera: true,
                    audio: true,
                    checking: false
                }));
                setTestStatus('Devices are ready! Please Wait ...');
            } catch (err) {
                setDeviceStatus(prevState => ({
                    ...prevState,
                    camera: false,
                    audio: false,
                    checking: false
                }));
                setTestStatus(`Failed to access devices: ${err.message}. Please check permissions.`);
                console.error("Failed to access devices:", err);
            }
        };
        getPermissions();
        
        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const checkDevices = async () => {
        setDeviceStatus(prevState => ({
            ...prevState,
            checking: true
        }));
        setTestStatus("Checking the devices...");
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true
            });
            
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            
            setDeviceStatus({
                camera: true,
                audio: true,
                checking: false
            });
            setTestStatus('Devices are ready! Please Wait ...');
        } catch (error) {
            console.error('Error checking devices:', error);
            setTestStatus('Error checking devices. Please refresh the page.');
            setDeviceStatus(prev => ({ 
                ...prev, 
                checking: false,
                camera: false,
                audio: false
            }));
        }
    };

    const startTest = async () => {
        if (!deviceStatus.camera) {
            alert('Please ensure your camera is working before starting the test.');
            return;
        }

        setIsRecording(true);
        setTestStatus('Starting recording...');

        try {
            const response = await fetch(`${backendUrl}/start_exam_recording`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, papercode })
            });

            if (response.ok) {
                // Start recording using MediaRecorder
                const mediaRecorder = new MediaRecorder(streamRef.current, {
                    mimeType: 'video/webm'
                });
                
                mediaRecorderRef.current = mediaRecorder;
                chunksRef.current = [];

                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        chunksRef.current.push(event.data);
                    }
                };

                mediaRecorder.onstop = async () => {
                    const blob = new Blob(chunksRef.current, { type: 'video/webm' });
                    const formData = new FormData();
                    formData.append('video', blob, 'recording.webm');
                    formData.append('name', name);
                    formData.append('papercode', papercode);

                    try {
                        const uploadResponse = await fetch(`${backendUrl}/upload_video_chunk`, {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (uploadResponse.ok) {
                            setTestStatus('Recording completed! You can now proceed with the test.');
                            localStorage.setItem("verified", true);
                            navigate('/rules');
                        }
                    } catch (error) {
                        console.error('Upload error:', error);
                        setTestStatus('Error uploading recording. Please try again.');
                    }
                };

                mediaRecorder.start(1000); // Collect chunks every second
                setTestStatus('Recording in progress... Please wait...');
            }
        } catch (error) {
            console.error(error);
            setIsRecording(false);
            setTestStatus('Error in recording. Please try again.');
        }
    };

    const stopTest = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.stop();
        }
        
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
        }
        
        setIsRecording(false);
        setTestStatus('Recording stopped.');
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
            <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="verification_webcam"
            />
            
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