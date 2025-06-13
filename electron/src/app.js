window.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copy-btn');
    const recordBtn = document.getElementById('record-btn');
    const retranscribeBtn = document.getElementById('retranscribe-btn');
    const recordBtnText = recordBtn.querySelector('span');
    const recordBtnIcon = recordBtn.querySelector('svg');
    const transcriptEl = document.getElementById('transcript');
    const discussionEl = document.getElementById('discussion-label');
    const renameBtn = document.getElementById('rename-btn');
    const saveNameBtn = document.getElementById('save-name-btn');
    const nameInput = document.getElementById('discussion-name-input');

    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    const RECORDING_DIR = path.join(os.tmpdir(), 'clearsay_recordings');
    // ``__dirname`` points to ``electron/src`` when running in the renderer
    // process. Step up two levels to reach the repository root where the
    // ``saved_data`` folder lives.
    const DISCUSSIONS_DIR = path.join(__dirname, '..', '..', 'saved_data', 'discussions');
    try {
        fs.mkdirSync(RECORDING_DIR, { recursive: true });
    } catch (_) {}

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
    let suppressLabelUpdate = false;
    const transcriptBuffer = [];

    async function updateDiscussionLabel() {
        if (suppressLabelUpdate) return;
        try {
            const res = await fetch(`http://localhost:${API_PORT}/current_discussion`);
            const data = await res.json();
            if (suppressLabelUpdate) return;
            if (data.id) {
                const label = data.name ? data.name : data.id;
                discussionEl.textContent = `Discussion: ${label}`;
                renameBtn.disabled = false;
                renameBtn.style.display = 'inline-flex';
                discussionEl.style.display = '';
                nameInput.style.display = 'none';
                saveNameBtn.style.display = 'none';
            } else {
                discussionEl.textContent = 'No active discussion';
                renameBtn.disabled = true;
                renameBtn.style.display = 'none';
                discussionEl.style.display = '';
                nameInput.style.display = 'none';
                saveNameBtn.style.display = 'none';
            }
        } catch (_) {
            if (suppressLabelUpdate) return;
            discussionEl.textContent = 'No active discussion';
            renameBtn.disabled = true;
            renameBtn.style.display = 'none';
            discussionEl.style.display = '';
            nameInput.style.display = 'none';
            saveNameBtn.style.display = 'none';
        }
    }

    updateDiscussionLabel();

    renameBtn.addEventListener('click', () => {
        const current = discussionEl.textContent.replace('Discussion: ', '').trim();
        nameInput.value = current;
        discussionEl.style.display = 'none';
        nameInput.style.display = 'inline';
        saveNameBtn.style.display = 'inline-flex';
        renameBtn.style.display = 'none';
        saveNameBtn.disabled = true;
    });

    nameInput.addEventListener('input', () => {
        const current = discussionEl.textContent.replace('Discussion: ', '').trim();
        saveNameBtn.disabled = nameInput.value.trim() === current;
    });

    saveNameBtn.addEventListener('click', async () => {
        const name = nameInput.value.trim();
        try {
            await fetch(`http://localhost:${API_PORT}/discussion_name`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name })
            });
            await updateDiscussionLabel();
        } catch (err) {
            console.error('Failed to rename discussion', err);
        }
        discussionEl.style.display = '';
        nameInput.style.display = 'none';
        saveNameBtn.style.display = 'none';
        renameBtn.style.display = 'inline-flex';
    });

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

    function getLatestSessionAudio() {
        try {
            const dirs = fs.readdirSync(DISCUSSIONS_DIR)
                .filter(d => {
                    try { return fs.statSync(path.join(DISCUSSIONS_DIR, d)).isDirectory(); }
                    catch { return false; }
                });
            if (dirs.length === 0) return [];
            dirs.sort();
            const latestDir = dirs[dirs.length - 1];
            const metaPath = path.join(DISCUSSIONS_DIR, latestDir, 'segments.json');
            const data = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            if (data && Array.isArray(data.segments)) {
                const segs = [...data.segments];
                segs.sort((a, b) => (a.id || '').localeCompare(b.id || ''));
                return segs.map(s => path.join(latestDir, s.wav));
            }
        } catch (err) {
            console.error('Failed to read segments', err);
        }
        return [];
    }

    function labelLatestDiscussion() {
        try {
            const dirs = fs.readdirSync(DISCUSSIONS_DIR)
                .filter(d => {
                    try { return fs.statSync(path.join(DISCUSSIONS_DIR, d)).isDirectory(); }
                    catch { return false; }
                });
            if (!dirs.length) return;
            dirs.sort();
            const latest = dirs[dirs.length - 1];
            const meta = path.join(DISCUSSIONS_DIR, latest, 'segments.json');
            const info = JSON.parse(fs.readFileSync(meta, 'utf8'));
            const label = info.name ? info.name : (info.created_at || latest);
            discussionEl.textContent = `Discussion: ${label}`;
            renameBtn.disabled = false;
            renameBtn.style.display = 'inline-flex';
        } catch (err) {
            console.error('Failed to set latest discussion label', err);
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
                        await updateDiscussionLabel();
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
        const files = getLatestSessionAudio();
        if (!files.length) {
            return;
        }
        try {
            processing = true;
            recordBtn.disabled = true;
            recordBtnText.textContent = 'Start Recording';
            recordBtnIcon.innerHTML = micIcon;
            retranscribeBtn.disabled = true;
            retranscribeBtn.textContent = 'Transcribing...';
            transcriptBuffer.length = 0;
            transcriptEl.innerHTML = '';

            suppressLabelUpdate = true;
            labelLatestDiscussion();
            await new Promise(r => setTimeout(r, 50));

            for (const [idx, file] of files.entries()) {
                const p = document.createElement('p');
                p.textContent = 'Transcribing...';
                transcriptEl.appendChild(p);
                try {
                    const res = await fetch(`http://localhost:${API_PORT}/transcribe?file=${encodeURIComponent(file)}`);
                    const data = await res.json();
                    const text = (data && data.transcript !== undefined) ? data.transcript : '';
                    transcriptBuffer.push(text);
                    if (idx === 0) {
                        suppressLabelUpdate = false;
                        await updateDiscussionLabel();
                    }
                    p.textContent = text;
                } catch (err) {
                    console.error('Failed to retranscribe', err);
                    p.textContent = '[error]';
                }
            }
        } finally {
            processing = false;
            recordBtn.disabled = false;
            retranscribeBtn.disabled = false;
            retranscribeBtn.textContent = 'Re-Transcribe';
            suppressLabelUpdate = false;
            await updateDiscussionLabel();
        }
    });
});
