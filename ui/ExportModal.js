import React, { useEffect } from 'react';
import './ExportModal.css';
import bufferManager from '../core/bufferManager';

export default function ExportModal({ open, onClose }) {
  useEffect(() => {
    if (!open) return;
    const handleKey = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onClose]);

  if (!open) return null;

  const handleOverlay = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const copyText = () => {
    const text = bufferManager.getFull();
    if (text) navigator.clipboard.writeText(text);
  };

  const saveFile = () => {
    const text = bufferManager.getFull();
    fetch('http://localhost:8000/export-docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    })
      .then(r => r.json())
      .then(() => alert('Saved'))
      .catch(() => alert('Error saving'));
  };

  const newDoc = () => {
    if (window.confirm('Clear current document?')) {
      bufferManager.reset();
      onClose();
    }
  };

  return (
    <div className="export-overlay" onClick={handleOverlay}>
      <div className="export-modal">
        <button className="tile" onClick={copyText}>Copy</button>
        <button className="tile" onClick={saveFile}>Save to file</button>
        <button className="tile" onClick={newDoc}>New Document</button>
      </div>
    </div>
  );
}
