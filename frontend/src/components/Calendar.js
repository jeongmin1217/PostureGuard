import React, { useCallback, useState, useEffect } from "react";
import classNames from "classnames/bind";
import { Link, useNavigate } from 'react-router-dom';
import style from '../styles/calendar.css';
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faFileAlt } from '@fortawesome/free-regular-svg-icons';
import { faHome } from '@fortawesome/free-solid-svg-icons';

const cx = classNames.bind(style);

const Calendar = () => {
  const today = {
    year: new Date().getFullYear(), //오늘 연도
    month: new Date().getMonth() + 1, //오늘 월
    date: new Date().getDate(), //오늘 날짜
    day: new Date().getDay(), //오늘 요일
  };
  const week = ["일", "월", "화", "수", "목", "금", "토"]; //일주일
  const [selectedYear, setSelectedYear] = useState(today.year); //현재 선택된 연도
  const [selectedMonth, setSelectedMonth] = useState(today.month); //현재 선택된 달
  const dateTotalCount = new Date(selectedYear, selectedMonth, 0).getDate(); //선택된 연도, 달의 마지막 날짜
  
  const [dataByMonth, setDataByMonth] = useState({}); // 연 단위로 가져온 데이터

  const navigate = useNavigate();

  useEffect(() => {
    checkDataForYear();
  }, [selectedYear]);

  const checkDataForYear = async () => {
    const response = await axios.get('http://localhost:8000/logs/check-date-data/', {
      params: {
        year_id: selectedYear,
      },
    });
    setDataByMonth(response.data.data_by_month);
  };

  const prevMonth = useCallback(() => {
    //이전 달 보기 보튼
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear(selectedYear - 1);
    } else {
      setSelectedMonth(selectedMonth - 1);
    }
  }, [selectedMonth]);

  const nextMonth = useCallback(() => {
    //다음 달 보기 버튼
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear(selectedYear + 1);
    } else {
      setSelectedMonth(selectedMonth + 1);
    }
  }, [selectedMonth]);

  const monthControl = useCallback(() => {
    //달 선택박스에서 고르기
    let monthArr = [];
    for (let i = 0; i < 12; i++) {
      monthArr.push(
        <option key={i + 1} value={i + 1}>
          {i + 1}
        </option>
      );
    }
    return (
      <select
        className="yearAndMonthSelect"
        onChange={changeSelectMonth}
        value={selectedMonth}
      >
        {monthArr}
      </select>
    );
  }, [selectedMonth]);

  const yearControl = useCallback(() => {
    //연도 선택박스에서 고르기
    let yearArr = [];
    const startYear = today.year - 10; //현재 년도부터 10년전 까지만
    const endYear = today.year + 10; //현재 년도부터 10년후 까지만
    for (let i = startYear; i < endYear + 1; i++) {
      yearArr.push(
        <option key={i} value={i}>
          {i}
        </option>
      );
    }
    return (
      <select
        className="yearAndMonthSelect"
        onChange={changeSelectYear}
        value={selectedYear}
      >
        {yearArr}
      </select>
    );
  }, [selectedYear]);

  const changeSelectMonth = (e) => {
    setSelectedMonth(Number(e.target.value));
  };
  const changeSelectYear = (e) => {
    setSelectedYear(Number(e.target.value));
  };

  const returnWeek = useCallback(() => {
    //요일 반환 함수
    let weekArr = [];
    week.forEach((v) => {
      weekArr.push(
        <div
          key={v}
          className={cx(
            { weekday: true },
            { sunday: v === "일" },
            { saturday: v === "토" }
          )}
        >
          {v}
        </div>
      );
    });
    return weekArr;
  }, []);

  const returnDay = useCallback(() => {
    //선택된 달의 날짜들 반환 함수
    let dayArr = [];

    for (const nowDay of week) {

      const day = new Date(selectedYear, selectedMonth - 1, 1).getDay();

      if (week[day] === nowDay) {

        for (let i = 0; i < dateTotalCount; i++) {
            // const currentDate = new Date(selectedYear, selectedMonth - 1, i + 2);
            // const dateString = currentDate.toISOString().split('T')[0];
            const dayNumber = i + 1;
            const daysWithData = dataByMonth[selectedMonth] || [];
            // console.log("dateString", dateString)  
            dayArr.push(
                <div
                key={i + 1}
                className={cx(
                    {
                    //오늘 날짜일 때 표시할 스타일 클라스네임
                    today:
                        today.year === selectedYear &&
                        today.month === selectedMonth &&
                        today.date === dayNumber,
                    },
                    { weekday: true }, //전체 날짜 스타일
                    {
                    //전체 일요일 스타일
                    sunday:
                        new Date(
                        selectedYear,
                        selectedMonth - 1,
                        dayNumber
                        ).getDay() === 0,
                    },
                    {
                    //전체 토요일 스타일
                    saturday:
                        new Date(
                        selectedYear,
                        selectedMonth - 1,
                        dayNumber
                        ).getDay() === 6,
                    }
                )}
                onClick={() => handleClickScore(dayNumber)} // 클릭 이벤트 핸들러 설정
                >
                {dayNumber}
                {/* 날짜 밑에 점 표시 */}
                {daysWithData.includes(dayNumber) && <span className="dot" style={{ color: "#6d62a3", cursor: "pointer", fontWeight: "bold" }}>•</span>}
                </div>
            );
        }
      } else {
        dayArr.push(<div className="weekday"></div>);
      }
    }
    return dayArr;
  }, [dataByMonth, selectedYear, selectedMonth, dateTotalCount]);

  function handleClickScore(day) {
    navigate(`/daily-report/${selectedYear}/${selectedMonth}/${day}`);
  }

  return (

    <div className="container">
        <div className="header-calendar">
            <div className='header-calendar-icon-div'>
                <img className="header-calendar-icon" src={`${process.env.PUBLIC_URL}/icon1.PNG`} alt="icon" />
            </div>
            <div className='header-calendar-main'>
                <div className='header-calendar-main-text'>
                    <p className='header-calendar-title'>Posture Guard</p>
                    <p className='header-calendar-description'>당신의 건강을 사수하세요!</p>
                </div>
                <div className='header-calendar-main-icon'>
                    <div className="selectionIcon">
                        <Link to="/">
                            <FontAwesomeIcon icon={faHome} style={{color: "#8871e6", fontSize:"27px"}} />
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
        <div className="calendar-main">
          <div className="title">
              <button onClick={prevMonth}>‹</button>
              <h3>{yearControl()}년 {monthControl()}월</h3>
              <button onClick={nextMonth}>›</button>
          </div>
          <div className="week">{returnWeek()}</div>
          <div className="date">{returnDay()}</div>
        </div>
        {/* <div className="bottom-bar">
          <button className="go-to-webcam"><Link to="/" style={{ color:"white", textDecoration: "none" }}>홈으로 돌아가기</Link></button>
        </div> */}
    </div>
  );
};

export default Calendar;