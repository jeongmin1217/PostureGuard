import React from 'react';
import { HashRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home';
import Calendar from './components/Calendar';
import Report from './components/Report';
import DailyReport from './components/DailyReport';
import './App.css';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/calendar" element={<Calendar />} />
                <Route path="/weekly-report" element={<Report />} />
                <Route path="/daily-report/:year/:month/:day" element={<DailyReport />} />
            </Routes>
        </Router>
    );
}

export default App;
