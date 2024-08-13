import React, { useRef, useState, useEffect } from 'react';
import '../styles/report.css';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCalendar } from '@fortawesome/free-regular-svg-icons';
import { Link } from 'react-router-dom';

function Report() {
  return (
    <div className="App-report">
        <div className="header-report">
            <div className='header-report-icon-div'>
                <img className="header-report-icon" src={`${process.env.PUBLIC_URL}/icon1.PNG`} alt="icon" />
            </div>
            <div className='header-report-main'>
                <div className='header-report-main-text'>
                    <p className='header-report-title'>지난 일주일간 평균 자세를 제공합니다</p>
                    <p className='header-report-description'>C7 포인트 : 경추 중 가장 돌출된 일곱 번째 경추뼈로, 자세 평가와 치료에서의 중요한 기준점</p>
                </div>
                <div className='header-report-main-icon'>
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
            </div>
            <div className="posture-container">
                <p className="posture-container-title">옳지 않은 자세의 평균 포인트</p>
                <div className="short-line"></div>
            </div>
        </div>

        <div className="controls-report">
            <button className="go-to-home"><Link to="/" style={{ color:"white", textDecoration: "none" }}>홈으로 돌아가기</Link></button>
        </div>
    </div>
    )
}

export default Report