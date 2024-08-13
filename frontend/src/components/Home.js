import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';
import '../styles/home.css';  // 필요한 경우 스타일 파일 포함
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendar, faFileAlt, faStickyNote } from '@fortawesome/free-regular-svg-icons';
import { Link } from 'react-router-dom';

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
                <div className='header-main'>
                    <div className='header-main-text'>
                        <p className='header-title'>Posture Guard</p>
                        <p className='header-description'>당신의 건강을 사수하세요!</p>
                    </div>
                    <div className='header-main-icon'>
                        <div className="selectionIcon">
                            <Link to="/calendar">
                                <FontAwesomeIcon icon={faCalendar} style={{color: "#8871e6", fontSize:"27px"}} />
                            </Link>
                        </div>
                        <div className="selectionIcon">
                            <Link to="/weekly-report">
                                <FontAwesomeIcon icon={faFileAlt} style={{color: "#8871e6", fontSize:"27px"}} />
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="main-content">
                <div className="camera-container">
                    <Webcam
                        audio={false}
                        ref={webcamRef}
                        screenshotFormat="image/jpeg"
                        className='camera-webcam'
                    />
                </div>
                <div className="description-container">
                    <p className="description-title">실시간 자세 분석</p>
                    <p className="description">
                        CVA : 경추의 정렬 상태 평가 지표<br></br>
                        FHA : 머리의 위치와 자세 평가 지표
                    </p>
                    <div className="description-grid">
                        <div className="description-box">
                            <p>CVA L</p>
                        </div>
                        <div className="description-box">
                            <p>-</p>
                        </div>
                        <div className="description-box">
                            <p>CVA R</p>
                        </div>
                        <div className="description-box">
                            <p>-</p>
                        </div>
                        <div className="description-box">
                            <p>FHA L</p>
                        </div>
                        <div className="description-box">
                            <p>-</p>
                        </div>
                        <div className="description-box">
                            <p>FHA R</p>
                        </div>
                        <div className="description-box">
                            <p>-</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="controls">
                <div className="controls-main">
                    <button onClick={startCameraCapture}>시작</button>
                    <div className="score">자세를 분석합니다</div>
                    <button onClick={stopCameraCapture}>종료</button>
                </div>
            </div>
        </div>
    );
}

export default Home;
