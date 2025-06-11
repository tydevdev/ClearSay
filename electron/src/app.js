window.addEventListener('DOMContentLoaded', () => {
    const copyBtn = document.getElementById('copy-btn');
    const transcript = document.getElementById('transcript');

    copyBtn.addEventListener('click', () => {
        const text = transcript.innerText.trim();
        if (text) {
            navigator.clipboard.writeText(text);
        }
    });
});
