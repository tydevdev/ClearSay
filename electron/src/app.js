window.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copy-btn');
    const recordBtn = document.getElementById('record-btn');
    const labelEl = recordBtn.querySelector('.label');
    const iconEl = recordBtn.querySelector('svg');
    const transcriptEl = document.getElementById('transcript');

    const API_PORT = 8000;

    const micIcon = `
        <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
        <line x1="12" y1="19" x2="12" y2="22"></line>
    `;

    const stopIcon = `
        <rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect>
    `;

    const States = {
        IDLE: 'idle',
        RECORDING: 'recording',
        PROCESSING: 'processing',
        ERROR: 'error'
    };
    let state = States.IDLE;
    let mediaRecorder;
    let chunks = [];

    function setState(newState) {
        state = newState;
        recordBtn.classList.remove('state-idle', 'state-recording', 'state-processing', 'state-error');
        recordBtn.classList.add(`state-${newState}`);
        switch (newState) {
            case States.IDLE:
                labelEl.textContent = 'Start Recording';
                iconEl.innerHTML = micIcon;
                recordBtn.disabled = false;
                break;
            case States.RECORDING:
                labelEl.textContent = 'Stop Recording';
                iconEl.innerHTML = stopIcon;
                recordBtn.disabled = false;
                break;
            case States.PROCESSING:
                labelEl.textContent = 'Processing...';
                iconEl.innerHTML = '';
                recordBtn.disabled = true;
                break;
            case States.ERROR:
                labelEl.textContent = 'Error';
                iconEl.innerHTML = micIcon;
                recordBtn.disabled = false;
                break;
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            chunks = [];
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = e => chunks.push(e.data);
            mediaRecorder.onstop = handleStop;
            mediaRecorder.start();
            setState(States.RECORDING);
        } catch (err) {
            console.error('Failed to start recording', err);
            setState(States.ERROR);
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
        }
    }

    async function handleStop() {
        setState(States.PROCESSING);
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', blob, 'recording.webm');
        try {
            const res = await fetch(`http://localhost:${API_PORT}/transcribe`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                throw new Error(data.detail || 'Transcription failed');
            }
            const text = data.text || data.transcript;
            if (text !== undefined) {
                appendTranscript(text);
                document.dispatchEvent(new CustomEvent('transcript-ready', { detail: text }));
                setState(States.IDLE);
            } else {
                throw new Error('No transcript returned');
            }
        } catch (err) {
            console.error('Failed to transcribe', err);
            setState(States.ERROR);
            setTimeout(() => setState(States.IDLE), 1500);
        }
    }

    function appendTranscript(text) {
        const p = document.createElement('p');
        p.textContent = text;
        transcriptEl.appendChild(p);
        transcriptEl.scrollTop = transcriptEl.scrollHeight;
    }

    function toggleRecording() {
        if (state === States.IDLE) {
            startRecording();
        } else if (state === States.RECORDING) {
            stopRecording();
        }
    }

    copyBtn.addEventListener('click', () => {
        const text = transcriptEl.innerText.trim();
        if (text) {
            navigator.clipboard.writeText(text);
        }
    });

    recordBtn.addEventListener('click', toggleRecording);

    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && document.activeElement === document.body) {
            e.preventDefault();
            toggleRecording();
        }
    });

    setState(States.IDLE);
});
