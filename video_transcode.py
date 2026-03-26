import argparse
import os
import sys
import subprocess
import glob
import re
import configparser

def parse_env_params(param_string):
    """Parse parameter string from .env file format"""
    params = {}
    # Extract key=value pairs from string like "{ encoder=h265, bitrate=5M, audio=aac, audio_bitrate=256k }"
    matches = re.findall(r'(\w+)=(\w+)', param_string)
    for key, value in matches:
        params[key] = value
    return params

def load_encoding_parameters(resolution):
    """Load encoding parameters for given resolution from .env"""
    config = configparser.ConfigParser()
    config.read('.env')
    
    if 'enc_param' not in config:
        print("Error: [enc_param] section not found in .env file")
        sys.exit(1)
    
    if resolution not in config['enc_param']:
        print(f"Error: Resolution '{resolution}' not found in .env file")
        print(f"Available resolutions: {', '.join(config['enc_param'].keys())}")
        sys.exit(1)
    
    param_string = config['enc_param'][resolution]
    params = parse_env_params(param_string)
    return params

def get_input_files(input_paths):
    """Get list of input video files from paths (files or directories)"""
    video_extensions = ('.mp4', '.mkv', '.mov', '.avi', '.flv', '.webm', '.m4v', '.ts')
    input_files = []
    
    for path in input_paths:
        if os.path.isdir(path):
            # Recursively find all video files in directory
            for ext in video_extensions:
                input_files.extend(glob.glob(os.path.join(path, f'*{ext}')))
                input_files.extend(glob.glob(os.path.join(path, f'**/*{ext}'), recursive=True))
        elif os.path.isfile(path):
            input_files.append(path)
        else:
            print(f"Warning: Path not found: {path}")
    
    # Remove duplicates and sort
    input_files = sorted(list(set(input_files)))
    return input_files

def transcode_video(input_file, output_file, params):
    """Transcode a single video file using FFmpeg"""
    # Build FFmpeg command with parameters from .env
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-c:v', f'lib{params.get("encoder", "h265")}',
        '-b:v', params.get('bitrate', '5M'),
        '-c:a', params.get('audio', 'aac'),
        '-b:a', params.get('audio_bitrate', '256k'),
        '-y',  # Overwrite output file
        output_file
    ]
    
    try:
        print(f"Transcoding: {input_file} -> {output_file}")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Transcoding completed: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Transcoding failed for {input_file}: {e}")
        return False

def concat_videos(video_list, output_file):
    """Concatenate multiple videos using FFmpeg concat demuxer"""
    # Create temporary file list for FFmpeg concat
    concat_file = 'concat_list.txt'
    with open(concat_file, 'w') as f:
        for video in video_list:
            # Escape single quotes in filename
            escaped_path = video.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_file,
        '-c', 'copy',
        '-y',
        output_file
    ]
    
    try:
        print(f"\nConcatenating {len(video_list)} videos...")
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ Concatenation completed: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Concatenation failed: {e}")
        return False
    finally:
        # Clean up concat file
        if os.path.exists(concat_file):
            os.remove(concat_file)

def cleanup_temp_files(temp_files):
    """Remove temporary transcoded files"""
    for file in temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Cleaned up: {file}")
        except Exception as e:
            print(f"Warning: Could not delete {file}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Transcode and concatenate videos using FFmpeg with parameters from .env'
    )
    parser.add_argument('out_video', help='Output video file name')
    parser.add_argument('resolution', help='Target resolution (e.g., 720p, 1080p, 1440p, 4K)')
    parser.add_argument('input_videos', nargs='+', help='Input video file(s) or directory(es)')
    parser.add_argument('--keep-temp', action='store_true', help='Keep temporary transcoded files')
    
    args = parser.parse_args()
    
    # Load encoding parameters from .env
    print(f"Loading encoding parameters for {args.resolution}...")
    params = load_encoding_parameters(args.resolution)
    print(f"Parameters: {params}")
    
    # Get all input files
    print(f"\nScanning input paths...")
    input_files = get_input_files(args.input_videos)
    
    if not input_files:
        print("Error: No video files found in provided paths")
        sys.exit(1)
    
    print(f"Found {len(input_files)} video file(s)")
    
    # Transcode each video
    temp_files = []
    transcoded_count = 0
    
    print(f"\nStarting transcoding process...")
    for input_file in input_files:
        temp_output = f'.temp_{os.path.basename(input_file)}'
        if transcode_video(input_file, temp_output, params):
            temp_files.append(temp_output)
            transcoded_count += 1
    
    if transcoded_count == 0:
        print("Error: No videos were successfully transcoded")
        sys.exit(1)
    
    # Concatenate all transcoded videos
    if not concat_videos(temp_files, args.out_video):
        print("Error: Failed to concatenate videos")
        sys.exit(1)
    
    # Clean up temporary files
    if not args.keep_temp:
        print("\nCleaning up temporary files...")
        cleanup_temp_files(temp_files)
    
    print(f"\n✓ All done! Output: {args.out_video}")

if __name__ == '__main__':
    main()