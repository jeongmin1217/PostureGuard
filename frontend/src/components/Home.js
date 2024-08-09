import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';
import '../styles/home.css';  // 필요한 경우 스타일 파일 포함

function Home() {
    const webcamRef = useRef(null);
    const [intervalId, setIntervalId] = useState(null);

    const startLogGeneration = () => {
        axios.get('http://localhost:8000/logs/start/')
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                console.error('There was an error starting log generation!', error);
            });
    };

    const stopLogGeneration = () => {
        axios.get('http://localhost:8000/logs/stop/')
            .then(response => {
                console.log(response.data);
            })
            .catch(error => {
                console.error('There was an error stopping log generation!', error);
            });
    };

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
            <header className="App-header">
                <h5>Control Log Generation</h5>
                <div className='log-generator-button'>
                    <button onClick={startLogGeneration}>Start Log eneration</button>
                    <button onClick={stopLogGeneration}>Stop Log Generation</button>
                </div>
                <h3>Control Camera Capture</h3>
                <div className='camera'>
                    <Webcam
                        audio={false}
                        ref={webcamRef}
                        screenshotFormat="image/jpeg"
                        width="100%"
                        height="100%"
                        className='camera-webcam'
                    />
                    <div className='camera-button'>
                        <button onClick={startCameraCapture}>Start Camera Capture</button>
                        <button onClick={stopCameraCapture}>Stop Camera Capture</button>
                    </div>
                </div>
            </header>
        </div>
    );
}

export default Home;
