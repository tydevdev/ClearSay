import React, { useState } from 'react';
import ExportModal from './ExportModal';
import HistoryDrawer from './HistoryDrawer';

export default function MainScreen() {
  const [showExport, setShowExport] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  return (
    <div className="main-screen">
      <button onClick={() => setShowExport(true)} className="done-btn">Done</button>
      <button onClick={() => setHistoryOpen(o => !o)}>History</button>
      <HistoryDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} />
      <ExportModal open={showExport} onClose={() => setShowExport(false)} />
    </div>
  );
}
