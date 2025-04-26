#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
source "$DIR/venv/bin/activate"
python "$DIR/bin/call_whisper_transcribe.py" "$@"
