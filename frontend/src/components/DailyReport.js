import React, { useRef, useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/report.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendar } from '@fortawesome/free-regular-svg-icons';
import { Link } from 'react-router-dom';
import { faHome, faSpinner } from '@fortawesome/free-solid-svg-icons';
import axios from 'axios';

function DailyReport() {
    const { year, month, day } = useParams(); // URL에서 year, month, day 파라미터를 받아옴
    const [reportData, setReportData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
      }, [year, month, day]);

    const fetchData = async () => {
        try {
            const response = await axios.get('http://localhost:8000/logs/get-daily-data/', {
                params: {
                    year_id: year,
                    month_id: month,
                    day_id: day,
                },
            });
            setReportData(response.data);
            setLoading(false);
            console.log(response.data);
        } catch (error) {
            console.error("Failed to fetch data", error);
            setLoading(false);
        }
    };

    if (!reportData) {
        return <div className="loading-icon">
            <FontAwesomeIcon icon={faSpinner} spin size="3x" />
            <p>데이터를 불러오는 중입니다</p>
        </div>
    }
    
    return (
        <div className="App-report">
            <div className="header-report">
                <div className='header-report-icon-div'>
                    <img className="header-report-icon" src={`${process.env.PUBLIC_URL}/icon1.PNG`} alt="icon" />
                </div>
                <div className='header-report-main'>
                    <div className='header-report-main-text'>
                        <p className='header-report-title'>{year}년 {month}월 {day}일의 평균 자세를 제공합니다</p>
                        <p className='header-report-description'>C7 포인트 : 경추 중 가장 돌출된 일곱 번째 경추뼈로, 자세 평가와 치료에서의 중요한 기준점</p>
                    </div>
                    <div className='header-report-main-icon'>
                        <div className="selectionIcon">
                            <Link to="/">
                                <FontAwesomeIcon icon={faHome} style={{color: "#8871e6", fontSize:"27px"}} />
                            </Link>
                        </div>
                        <div className="selectionIcon-report">
                            <Link to="/calendar">
                                <FontAwesomeIcon icon={faCalendar} style={{color: "#8871e6", fontSize:"27px"}} />
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            <div className="main-content-report">
                <div className="posture-container">
                    <p className="posture-container-title">옳은 자세의 평균 포인트</p>
                    <div className="short-line"></div>
                    <img src={`https://storage.googleapis.com/posture-guard/daily-average-image/${reportData.correct_img_filename}`} alt="Correct Posture" />
                </div>
                <div className="posture-container">
                    <p className="posture-container-title">옳지 않은 자세의 평균 포인트</p>
                    <div className="short-line"></div>
                    <img src={`https://storage.googleapis.com/posture-guard/daily-average-image/${reportData.incorrect_img_filename}`} alt="Incorrect Posture" />
                </div>
            </div>

            <div className="controls-report">
                <p className="report-score">일간 점수 : {reportData.score}점</p>
            </div>
        </div>
        )
}

export default DailyReport