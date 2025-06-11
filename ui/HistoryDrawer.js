import React, { useEffect, useState } from 'react';
import './HistoryDrawer.css';

const API_BASE = 'http://localhost:8000';

export default function HistoryDrawer({ open, onClose }) {
  const [files, setFiles] = useState([]);
  const [content, setContent] = useState('');

  useEffect(() => {
    if (!open) return;
    fetch(`${API_BASE}/list-transcripts`)
      .then(r => r.json())
      .then(data => setFiles(data.files || []))
      .catch(() => setFiles([]));
  }, [open]);

  const loadFile = name => {
    fetch(`${API_BASE}/get-transcript?name=${encodeURIComponent(name)}`)
      .then(r => r.json())
      .then(data => setContent(data.content || ''))
      .catch(() => setContent(''));
  };

  return (
    <div className={`history-drawer${open ? ' open' : ''}`}>\
      <div className="drawer-header">
        <button onClick={onClose}>Close</button>
      </div>
      <div className="drawer-body">
        <ul className="file-list">
          {files.map(f => (
            <li key={f.name}>
              <button onClick={() => loadFile(f.name)}>{f.name}</button>
            </li>
          ))}
        </ul>
        <pre className="file-content">{content}</pre>
      </div>
    </div>
  );
}
