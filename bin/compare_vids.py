import os
import sys  # DO NOT REMOVE THIS — critical for sys.path and utils
import json
import difflib
import logging

# === Load from local utils ===
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, "../lib/python_utils")
sys.path.append(lib_path)

from transcription_utils import (
    whisper_transcribe_full_video,
    whisper_transcribe_video_by_minute,
)
from utilities1 import (
    initialize_logging,
    load_app_config,
    create_subdir,
)


def generate_comparison_report(file1_path, file2_path, output_path):
    with open(file1_path, "r") as f1, open(file2_path, "r") as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

    max_lines = max(len(lines1), len(lines2))
    report_lines = []

    for i in range(max_lines):
        line1 = lines1[i].strip() if i < len(lines1) else "[MISSING]"
        line2 = lines2[i].strip() if i < len(lines2) else "[MISSING]"

        if line1 == line2:
            report_lines.append(f"=== LINE {i + 1} ===\n✅ IDENTICAL: {line1}\n")
        else:
            report_lines.append(f"=== LINE {i + 1} ===")
            report_lines.append(f"🎥 1: {line1}")
            report_lines.append(f"🎥 2: {line2}")
            report_lines.append("🔍 DIFF:")
            for d in difflib.ndiff([line1], [line2]):
                report_lines.append(f"    {d}")
            report_lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(report_lines))

    print(f"\n📄 Comparison report saved to: {output_path}")


def main():
    logger = initialize_logging()
    config = load_app_config()

    # Locate the videos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "../data")
    video_files = [f for f in os.listdir(data_dir) if "watermarked" in f and f.endswith(".mp4")]

    if len(video_files) != 2:
        raise ValueError("Expected exactly two '*_watermarked.mp4' files in ./data")

    video_files.sort()
    video_paths = [os.path.join(data_dir, vf) for vf in video_files]
    print(f"Found videos:\n1. {video_files[0]}\n2. {video_files[1]}")

    # Build output path
    compare_id = f"{os.path.splitext(video_files[0])[0]}_vs_{os.path.splitext(video_files[1])[0]}"
    base_output_dir = create_subdir(base_dir="sources", subdir_name=compare_id)

    transcript_paths = []

    for video_path in video_paths:
        video_name = os.path.splitext(os.path.basename(video_path))[0]

        # Full transcript
        print(f"\n🎬 Transcribing (full): {video_name}")
        full_transcript = whisper_transcribe_full_video(video_path)
        full_out_path = os.path.join(data_dir, f"{video_name}.full.txt")
        with open(full_out_path, "w") as f:
            f.write(full_transcript)
        print(f"📝 Full transcript saved to {full_out_path}")
        transcript_paths.append(full_out_path)

        # Minute-by-minute transcript
        print(f"🕒 Transcribing (by minute): {video_name}")
        minute_transcript = whisper_transcribe_video_by_minute(video_path)
        minute_out_path = os.path.join(data_dir, f"{video_name}.minute.json")
        with open(minute_out_path, "w") as f:
            json.dump(minute_transcript, f, indent=2)
        print(f"📝 Minute-by-minute transcript saved to {minute_out_path}")

    # Generate comparison report
    print("\n🔍 Generating comparison report...")
    report_path = os.path.join(data_dir, "comparison_report.txt")
    generate_comparison_report(transcript_paths[0], transcript_paths[1], report_path)


if __name__ == "__main__":
    main()
