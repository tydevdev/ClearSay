const fs = require('fs');
const path = require('path');
const EventEmitter = require('events');

const TRANSCRIPT_DIR = path.join(__dirname, '..', 'transcripts');
const AUDIO_DIR = path.join(__dirname, '..', 'audio');

function pad(num) {
  return String(num).padStart(2, '0');
}

function formatTimestamp(date) {
  return (
    date.getFullYear() +
    '-' +
    pad(date.getMonth() + 1) +
    '-' +
    pad(date.getDate()) +
    '_' +
    pad(date.getHours()) +
    '-' +
    pad(date.getMinutes())
  );
}

class BufferManager extends EventEmitter {
  constructor() {
    super();
    this.parts = [];
    this.baseTimestamp = null;
    this.counter = 1;
  }

  append(text, wavPath) {
    if (!text) return;

    if (!this.baseTimestamp) {
      this.baseTimestamp = formatTimestamp(new Date());
    }

    this.parts.push(text.trim());
    const fullText = this.parts.join('\n\n');

    fs.mkdirSync(TRANSCRIPT_DIR, { recursive: true });
    const transcriptFile = path.join(
      TRANSCRIPT_DIR,
      `${this.baseTimestamp}.txt`
    );
    fs.writeFileSync(transcriptFile, fullText);

    if (wavPath && fs.existsSync(wavPath)) {
      fs.mkdirSync(AUDIO_DIR, { recursive: true });
      const dest = path.join(
        AUDIO_DIR,
        `${this.baseTimestamp}_${String(this.counter).padStart(3, '0')}.wav`
      );
      try {
        fs.renameSync(wavPath, dest);
      } catch (err) {
        // ignore errors when moving audio
      }
    }

    this.counter += 1;
    this.emit('buffer-updated', fullText);
  }

  getFull() {
    return this.parts.join('\n\n');
  }
}

module.exports = new BufferManager();
