import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';
import '../styles/home.css';  // 필요한 경우 스타일 파일 포함

function Home() {
    const webcamRef = useRef(null);
    const [intervalId, setIntervalId] = useState(null);

    const startCameraCapture = () => {
        if (intervalId) return;  // 이미 시작된 경우 중복 실행 방지

        const capture = async () => {
            const imageSrc = webcamRef.current.getScreenshot();
            try {
                await axios.post('http://localhost:8000/logs/send-image/', { image: imageSrc });
                console.log('Image sent to server');
            } catch (error) {
                console.error('There was an error sending the image!', error);
            }
        };
        const id = setInterval(capture, 1000); // 1초 간격으로 이미지 캡처 및 전송
        setIntervalId(id);
        console.log('Capture started');
    };

    const stopCameraCapture = () => {
        if (intervalId) {
            clearInterval(intervalId); // 캡처 중지
            setIntervalId(null);
            console.log('Capture stopped');
        }
    };

    // Clean up interval on unmount
    useEffect(() => {
        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
        };
    }, [intervalId]);

    return (
        <div className="App">
            <div className="header">
                <div className='header-icon-div'>
                    <img className="header-icon" src={`${process.env.PUBLIC_URL}/icon1.PNG`} alt="icon" />
                </div>
                <div className='header-text'>
                    <p className='header-title'>Posture Guard</p>
                    <p className='header-description'>당신의 건강을 사수하세요!</p>
                </div>
            </div>

            <div className="camera-container">
                <Webcam
                    audio={false}
                    ref={webcamRef}
                    screenshotFormat="image/jpeg"
                    className='camera-webcam'
                />
            </div>

            <div className="controls">
                <button onClick={startCameraCapture}>시작</button>
                <div className="score">Score: 0</div>
                <button onClick={stopCameraCapture}>종료</button>
            </div>
        </div>
    );
}

export default Home;
