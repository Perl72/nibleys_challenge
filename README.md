# Mimesis – Audio Transcription + Source Comparison Toolkit

## Quickstart

1. Set up environment:
    ./setup_venv.sh

2. Run full transcription:
    ./run.sh data/original.mp4

Outputs:
- Full transcript (.txt)
- Per-minute JSON
- Captions (.srt, .vtt)
- Source article scrape

## Project Structure

bin/        # Scripts (transcribe, captions, etc.)
conf/       # Configs
data/       # Media input
lib/        # Local Python packages
run.sh      # Run the pipeline
setup_venv.sh   # One-line environment setup
requirements.txt

## Requirements

- Python 3.9+
- ffmpeg
- OpenAI Whisper:
    pip install git+https://github.com/openai/whisper.git
- Others:
    pip install -r requirements.txt

## Credits

Developed by The Tim Ballard Defamation League – March 2025

mimesis/
├── bin/               # CLI scripts
├── conf/              # Configs
├── data/              # Media input
├── lib/               # Local modules (Acme/, python_utils/)
├── README.md          # ✔️ Exists
├── requirements.txt   # ✔️ Exists

mimesis-cougars/
├── bin/
│   └── compare_vids.py
├── data/
│   ├── Tim_Ballard_20241026_watermarked.mp4
│   ├── Tim_Ballard_20250424_watermarked.mp4
│   └── [transcripts + report will be saved here]
└── lib/
    └── python_utils/
        └── utilities1.py  ← with your patched create_subdir()



