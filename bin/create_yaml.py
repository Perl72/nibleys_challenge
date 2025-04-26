import yaml
import os
import re

# Function to parse time input and convert it to seconds
def parse_time(value):
    """Converts input to seconds if it's a number, otherwise assumes HH:MM:SS format."""
    if isinstance(value, (int, float)) or value.isdigit():
        return int(value)  # Assume it's already in seconds
    
    if ':' in value:  # Assume it's in HH:MM:SS or MM:SS format
        parts = list(map(int, value.split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        else:
            raise ValueError("Invalid time format: Expected HH:MM:SS or MM:SS")
    
    raise ValueError("Unrecognized time format")

# Function to collect clip data
def collect_clip_data():
    """Automatically generates clips and stores them in the required format."""
    clips_data = {}  # Dictionary to store all clips
    clip_number = 1  # Start clip numbering from 1

    while True:
        print(f"\nAdding clip_{clip_number}")
        start = input("Enter Start time (seconds or HH:MM:SS, or 'q' to quit): ").strip().lower()
        if start in ['q', 'quit']:
            print("Exiting clip entry.")
            break
        
        try:
            start_time = parse_time(start)
        except ValueError as e:
            print(f"Invalid start time input: {e}")
            continue
        
        end = input("Enter End time (seconds or HH:MM:SS, blank if none): ").strip()
        end_time = None
        if end:
            try:
                end_time = parse_time(end)
            except ValueError as e:
                print(f"Invalid end time input: {e}")
                continue
        
        text = input("Enter Clip text (Press Enter for no clip text): ").strip()
        
        clip_entry = [{'start': start_time, 'text': text}]
        if end_time is not None:
            clip_entry[0]['end'] = end_time
        
        clips_data[f'clip_{clip_number}'] = clip_entry
        print(f"Added clip: {clip_entry}")
        clip_number += 1  # Increment clip number globally
    
    return clips_data if clips_data else None

# Function to save the collected data to a YAML file
def save_to_yaml(data, file_path):
    """Saves data to a specified YAML file."""
    if data is None:
        print("No data to save. Exiting.")
        return
    
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                existing_data = yaml.safe_load(f) or {}
        else:
            existing_data = {}
        
        existing_data.update(data)
        
        with open(file_path, 'w') as f:
            yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"Clips saved to {file_path}.")
    except OSError as e:
        print(f"File error: {e}. Check file permissions and directory access.")

# Function to load and display YAML data
def yaml_to_dict(file_path):
    """Reads a YAML file and converts it into a dictionary."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
        print("Loaded YAML data:", data)
        return data
    except Exception as e:
        print(f"Error reading YAML file: {e}")
        return None

# Main script execution
if __name__ == "__main__":
    clips_dir = "clips/"  # Lexical variable for directory
    os.makedirs(clips_dir, exist_ok=True)  # Ensure directory exists
    
    file_name = input("Enter the filename to save clips (default: clips.yaml): ").strip()
    if not file_name:
        file_name = "clips.yaml"
    
    file_path = os.path.join(clips_dir, file_name)  # Compose full path
    
    new_data = collect_clip_data()
    save_to_yaml(new_data, file_path)
    
    data_dict = yaml_to_dict(file_path)
    print("Final Clip Data:", data_dict)
