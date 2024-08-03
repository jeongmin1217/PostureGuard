import './App.css';
import React, { useState } from 'react';
import axios from 'axios';

function App() {
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

    return (
        <div className="App">
            <header className="App-header">
                <h1>Control Log Generation</h1>
                <div className='log-generator-button'>
                    <button onClick={startLogGeneration}>Start Log Generation</button>
                    <button onClick={stopLogGeneration}>Stop Log Generation</button>
                </div>
            </header>
        </div>
    );
}

export default App;
