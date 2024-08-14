import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';
import '../styles/home.css';  // 필요한 경우 스타일 파일 포함
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendar, faFileAlt } from '@fortawesome/free-regular-svg-icons';
import { Link } from 'react-router-dom';
import { faSpinner } from '@fortawesome/free-solid-svg-icons';

function Home() {
    const webcamRef = useRef(null);
    const [intervalId, setIntervalId] = useState(null);
    const allowUpdates = useRef(true);  // 상태 업데이트를 제어할 플래그
    const [loading, setLoading] = useState(true);
    const [cvaLeft, setCvaLeft] = useState('-');
    const [cvaRight, setCvaRight] = useState('-');
    const [fhaLeft, setFhaLeft] = useState('-');
    const [fhaRight, setFhaRight] = useState('-');
    const [postureMessage, setPostureMessage] = useState('자세를 분석합니다');

    useEffect(() => {
        setLoading(false);

        // WebSocket 연결 설정
        const socket = new WebSocket('ws://210.123.95.211:8000/ws/logs/');

        socket.onmessage = function(event) {
            if (!allowUpdates.current) return;  // 상태 업데이트가 허용되지 않으면 종료

            const data = JSON.parse(event.data);

            // 수신된 데이터로 상태 업데이트
            setCvaLeft(data.cva_left);
            setCvaRight(data.cva_right);
            setFhaLeft(data.fha_left);
            setFhaRight(data.fha_right);

            // posture_correct 값에 따라 메시지 설정
            if (data.posture_correct === 'Yes') {
                setPostureMessage('옳은 자세입니다');
            } else if (data.posture_correct === 'No') {
                setPostureMessage('자세를 바르게 해주세요');
            }
        };

        return () => {
            socket.close(); // 컴포넌트 언마운트 시 소켓 연결 해제
        };
    }, []);

    const startCameraCapture = () => {
        if (intervalId) return;  // 이미 시작된 경우 중복 실행 방지
        // 상태 업데이트 허용
        allowUpdates.current = true;


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
        // 상태 업데이트 중지
        allowUpdates.current = false;

        setCvaLeft('-');
        setCvaRight('-');
        setFhaLeft('-');
        setFhaRight('-');
        setPostureMessage('자세를 분석합니다');
    };

    // 카메라가 처음 렌더링된 후 로딩 상태 해제
    useEffect(() => {
        setLoading(false);
    }, []);


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
                            <Link to="/report">
                                <FontAwesomeIcon icon={faFileAlt} style={{color: "#8871e6", fontSize:"27px"}} />
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="main-content">
                <div className="camera-container">
                    {loading ? (
                        <div className="loading-icon">
                            <FontAwesomeIcon icon={faSpinner} spin size="3x" />
                            <p>카메라 로딩 중</p>
                        </div>
                    ) : (
                        <Webcam
                            audio={false}
                            ref={webcamRef}
                            screenshotFormat="image/jpeg"
                            className='camera-webcam'
                        />
                    )}
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
                            <p>{cvaLeft}</p>
                        </div>
                        <div className="description-box">
                            <p>CVA R</p>
                        </div>
                        <div className="description-box">
                            <p>{cvaRight}</p>
                        </div>
                        <div className="description-box">
                            <p>FHA L</p>
                        </div>
                        <div className="description-box">
                            <p>{fhaLeft}</p>
                        </div>
                        <div className="description-box">
                            <p>FHA R</p>
                        </div>
                        <div className="description-box">
                            <p>{fhaRight}</p>
                        </div>
                    </div>
                </div>
            </div>

            <div className="controls">
                <div className="controls-main">
                    <button onClick={startCameraCapture}>시작</button>
                    <div className="score">{postureMessage}</div>
                    <button onClick={stopCameraCapture}>종료</button>
                </div>
            </div>
        </div>
    );
}

export default Home;
