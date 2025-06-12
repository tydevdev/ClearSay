window.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copy-btn');
    const recordBtn = document.getElementById('record-btn');
    const retranscribeBtn = document.getElementById('retranscribe-btn');
    const recordBtnText = recordBtn.querySelector('span');
    const recordBtnIcon = recordBtn.querySelector('svg');
    const transcriptEl = document.getElementById('transcript');

    const fs = require('fs');
    const path = require('path');
    const RECORDING_DIR = path.join(__dirname, '..', 'saved_data', 'recorded_audio');

    const API_PORT = 8000;

    const micIcon = `
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
        <line x1="12" y1="19" x2="12" y2="22"></line>
    `;

    const stopIcon = `
        <rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>
    `;

    let recording = false;
    let processing = false;
    const transcriptBuffer = [];

    function getLatestAudio() {
        try {
            const files = fs.readdirSync(RECORDING_DIR)
                .filter(f => f.toLowerCase().endsWith('.wav'));
            if (files.length === 0) return null;
            files.sort().reverse();
            return files[0];
        } catch (err) {
            console.error('Failed to read recordings', err);
            return null;
        }
    }

    copyBtn.addEventListener('click', () => {
        const text = transcriptEl.innerText.trim();
        if (text) {
            navigator.clipboard.writeText(text);
        }
    });

    recordBtn.addEventListener('click', async () => {
        if (processing) {
            return;
        }

        if (!recording) {
            // Start recording
            try {
                await fetch(`http://localhost:${API_PORT}/record`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'start' })
                });
                recording = true;
                recordBtnText.textContent = 'Stop Recording';
                recordBtnIcon.innerHTML = stopIcon;
            } catch (err) {
                console.error('Failed to start recording', err);
            }
        } else {
            // Stop recording
            try {
                const res = await fetch(`http://localhost:${API_PORT}/record`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'stop' })
                });
                const data = await res.json();

                processing = true;
                recording = false;
                recordBtnText.textContent = 'Processing...';
                recordBtnIcon.innerHTML = '';
                recordBtn.disabled = true;
                await new Promise(r => setTimeout(r, 50));

                if (data && data.file) {
                    const tRes = await fetch(`http://localhost:${API_PORT}/transcribe?file=${encodeURIComponent(data.file)}`);
                    const tData = await tRes.json();
                    if (tData && tData.transcript !== undefined) {
                        transcriptBuffer.push(tData.transcript);
                        transcriptEl.innerHTML = transcriptBuffer.map(t => `<p>${t}</p>`).join('');
                    }
                }
            } catch (err) {
                console.error('Failed to stop recording', err);
            } finally {
                processing = false;
                recordBtn.disabled = false;
                recordBtnText.textContent = 'Start Recording';
                recordBtnIcon.innerHTML = micIcon;
            }
        }
    });

    retranscribeBtn.addEventListener('click', async () => {
        if (processing) return;
        const latest = getLatestAudio();
        if (!latest) {
            return;
        }
        try {
            processing = true;
            recordBtn.disabled = true;
            retranscribeBtn.disabled = true;
            retranscribeBtn.textContent = 'Processing...';
            const res = await fetch(`http://localhost:${API_PORT}/transcribe?file=${encodeURIComponent(latest)}`);
            const data = await res.json();
            if (data && data.transcript !== undefined) {
                transcriptBuffer.push(data.transcript);
                transcriptEl.innerHTML = transcriptBuffer.map(t => `<p>${t}</p>`).join('');
            }
        } catch (err) {
            console.error('Failed to retranscribe', err);
        } finally {
            processing = false;
            recordBtn.disabled = false;
            retranscribeBtn.disabled = false;
            retranscribeBtn.textContent = 'Re-Transcribe';
        }
    });
});
