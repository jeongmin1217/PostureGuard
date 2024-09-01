import React, { useState } from 'react';
import '../styles/home.css';  // 필요한 경우 스타일 파일 포함

function Modal({ isOpen, onClose, message }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal">
        <p>{message}</p>
        <button onClick={onClose}>닫기</button>
      </div>
    </div>
  );
}

export default Modal;
