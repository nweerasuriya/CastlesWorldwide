"""
Automated Video Creation with AI voiceover and subtitles
Data comes from a CSV file - Fixed version with subtitle display issues resolved
Added subtitle delay and changed color to orange
"""

__date__ = "2025-05-04"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.3"

import os
import azure.cognitiveservices.speech as speechsdk
import pandas as pd
import requests
import subprocess
import time
import json
import tempfile
from ast import literal_eval


def generate_azure_voice_with_subtitles(text, audio_output_path, srt_output_path, voice_name="en-GB-OllieMultilingualNeural"):
    """
    Generate speech from text using Azure Speech Service with a British male voice,
    while simultaneously creating SRT subtitle file with accurate word timing.
    
    Parameters:
    - text: The text to convert to speech
    - audio_output_path: Where to save the audio file
    - srt_output_path: Where to save the SRT subtitle file
    - voice_name: The Azure voice to use
    
    Returns:
    - Tuple: (audio_path, srt_path) or (None, None) on failure
    """
    import os
    import azure.cognitiveservices.speech as speechsdk
    import re
    
    # Your Azure Speech Service subscription key and region
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    service_region = "uksouth"
    
    # Function to format time in SRT format (HH:MM:SS,mmm)
    def format_srt_time(seconds):
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        seconds_remainder = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds_remainder:06.3f}".replace(".", ",")
    
    # Function to split text into meaningful segments (sentences or phrases)
    def split_into_segments(text, max_length=10):
        # Split by sentence endings (., !, ?) followed by a space or newline
        raw_segments = re.split(r'([,.!?][\s\n])', text)
        segments = []
        
        current_segment = ""
        for i in range(0, len(raw_segments), 2):
            if i < len(raw_segments):
                part = raw_segments[i]
                # Add the punctuation back if it exists
                if i + 1 < len(raw_segments):
                    part += raw_segments[i + 1]
                
                # If adding this part would make the segment too long, start a new one
                if len(current_segment) + len(part) > max_length and current_segment:
                    segments.append(current_segment.strip())
                    current_segment = part
                else:
                    current_segment += part
        
        # Add the last segment if it's not empty
        if current_segment.strip():
            segments.append(current_segment.strip())
            
        return segments
    
    try:
        # Configure speech configuration
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        speech_config.speech_synthesis_voice_name = voice_name
        
        # Configure audio output
        audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_output_path)
        
        # Create speech synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        
        # Split the text into segments
        segments = split_into_segments(text)
        
        # Prepare for SRT generation
        srt_entries = []
        current_entry = 1
        
        # Process each segment separately to create better subtitle chunks
        for segment_idx, segment in enumerate(segments):
            # Track timing data for this segment
            segment_start_time = None
            segment_end_time = None
            segment_words = []
            
            # Set up word boundary event handler
            def word_boundary_event_handler(evt):
                nonlocal segment_start_time, segment_end_time
                # Convert from ticks (100-nanosecond units) to seconds
                time_in_seconds = evt.audio_offset / 10000000
                duration_in_seconds = evt.duration.total_seconds()
                
                # Track first word's start time
                if segment_start_time is None:
                    segment_start_time = time_in_seconds
                
                # Always update the end time with the last word's end
                segment_end_time = time_in_seconds + duration_in_seconds + 0.2
                
                # Store the word and its timing
                segment_words.append({
                    'word': evt.text,
                    'start': time_in_seconds,
                    'end': time_in_seconds + duration_in_seconds
                })
            
            # Connect the event handler
            synthesizer.synthesis_word_boundary.connect(word_boundary_event_handler)
            
            # Generate speech for this segment
            result = synthesizer.speak_text_async(segment).get()
            
            # Check result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # If we have valid timing data, create an SRT entry
                if segment_start_time is not None and segment_end_time is not None:
                    # Handle segment offset relative to audio start for segments after the first
                    if segment_idx > 0 and srt_entries:
                        # Get last entry's end time as our reference
                        last_end_time = srt_entries[-1]['end']
                        
                        # Adjust timing to be continuous
                        time_offset = last_end_time - segment_start_time
                        segment_start_time += time_offset
                        segment_end_time += time_offset
                    
                    # Create SRT entry - Remove html.escape() to fix apostrophes
                    srt_entries.append({
                        'number': current_entry,
                        'start': segment_start_time,
                        'end': segment_end_time,
                        'text': segment  # No HTML escaping for plain text SRT
                    })
                    current_entry += 1
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                print(f"Speech synthesis canceled: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    print(f"Error details: {cancellation_details.error_details}")
                return None, None

        # Write the SRT file
        with open(srt_output_path, 'w', encoding='utf-8') as srt_file:
            for entry in srt_entries:
                srt_file.write(f"{entry['number']}\n")
                srt_file.write(f"{format_srt_time(entry['start'])} --> {format_srt_time(entry['end'])}\n")
                srt_file.write(f"{entry['text']}\n\n")
        
        print(f"Speech synthesized to {audio_output_path}")
        print(f"Subtitles created at {srt_output_path}")
        return audio_output_path, srt_output_path
    
    except Exception as e:
        print(f"Error generating speech and subtitles: {str(e)}")
        return None, None

def download_image(image_url, image_path):
    """
    Download an image from a URL to a local path.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    response = requests.get(image_url, stream=True, headers=headers)
    if response.status_code == 200:
        with open(image_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        return True
    else:
        print(f"Failed to download image: {response.status_code}")
        return False

def get_audio_duration(audio_path):
    """
    Get the duration of an audio file using ffprobe.
    """
    cmd = [
        'ffprobe', 
        '-i', audio_path, 
        '-show_entries', 'format=duration',
        '-v', 'quiet',
        '-of', 'csv=p=0'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        return float(result.stdout.strip())
    return None

def create_castle_video(image_paths, audio_path, subtitle_path, output_path, castle_name):
    """
    Create a TikTok-style video with background images and synced subtitles.
    Using crossfade transitions between images.
    
    Parameters:
    - image_paths: List of paths to image files
    - audio_path: Path to the audio file
    - subtitle_path: Path to subtitle file in SRT format
    - output_path: Path where the final video will be saved
    - castle_name: Name of the castle to display at the beginning
    
    Returns:
    - Boolean indicating success or failure
    """
    import os
    import subprocess
    import tempfile
    
    # Get audio duration
    duration = get_audio_duration(audio_path)
    if not duration:
        print("Could not determine audio duration")
        return False
    
    total_duration = duration
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Scale and pad all images to 1080x1920 (vertical video format)
        scaled_images = []
        for i, img_path in enumerate(image_paths):
            scaled_path = os.path.join(temp_dir, f"scaled_{i}.jpg")
            scale_cmd = [
                'ffmpeg', '-y',
                '-i', img_path,
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,'
                       'pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
                scaled_path
            ]
            try:
                subprocess.run(scale_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                scaled_images.append(scaled_path)
            except subprocess.CalledProcessError as e:
                print(f"Error scaling image {i}: {e}")
        
        if not scaled_images:
            print("No images were successfully scaled")
            return False
        
        # Calculate duration per image (excluding transitions)
        num_images = len(scaled_images)
        transition_duration = 1.0  # 1 second crossfade
        
        # Calculate how long each image should be shown
        total_show_time = duration - ((num_images - 1) * transition_duration)
        image_duration = total_show_time / num_images if num_images > 0 else duration
        
        # Create subtitle ASS file with more flexibility than SRT
        ass_path = os.path.join(temp_dir, "subtitles.ass")
        
        # Convert SRT to ASS format using FFmpeg (more reliable for embedding)
        if subtitle_path and os.path.exists(subtitle_path):
            convert_cmd = [
                'ffmpeg', '-y',
                '-i', subtitle_path,
                ass_path
            ]
            try:
                subprocess.run(convert_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"Converted subtitles to ASS format: {ass_path}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting subtitles to ASS: {e}")
                # If conversion fails, we'll try to use the SRT directly
                ass_path = subtitle_path
        
        # Create a filter complex string directly instead of using a file
        filter_complex = []
        
        # Input section for each image
        for i in range(num_images):
            filter_complex.append(f"[{i}:v]format=yuv420p,fps=30[v{i}];")
        
        # Chain the crossfades
        last_output = "v0"
        for i in range(1, num_images):
            offset = i * image_duration + (i - 1) * transition_duration
            filter_complex.append(f"[{last_output}][v{i}]xfade=transition=fade:duration={transition_duration}:offset={offset}[v{i}out];")
            last_output = f"v{i}out"
        
        # Add fade in/out and castle name
        filter_complex.append(f"[{last_output}]fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1")
        
        # Add subtitle if subtitle file exists and is accessible
        if subtitle_path and os.path.exists(subtitle_path):
            # Use subtitles filter directly in the filter_complex
            subtitle_escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
            filter_complex.append(
                # centre the subtitles and set font properties
                f",subtitles='{subtitle_escaped}':force_style='Fontname=Arial,Fontsize=10,Bold=1,Alignment=2,"
                f"PrimaryColour=&H008AFF,OutlineColour=&H000000,BorderStyle=1,Outline=2,Shadow=0,MarginV=50'"
            )
        # Always end with the output label
        filter_complex.append("[vout]")
        
        # Join all filter complex parts
        filter_complex_str = "".join(filter_complex)
        
        # Create input arguments for each scaled image
        input_args = []
        for img in scaled_images:
            input_args.extend(['-loop', '1', '-t', str(total_duration), '-i', img])
        
        # Combine images, audio, and apply filters
        cmd = [
            'ffmpeg', '-y',
            *input_args,
            '-i', audio_path,
            '-filter_complex', filter_complex_str,
            '-map', '[vout]',
            '-map', f'{num_images}:a',  # Audio comes after all images
            '-c:v', 'libx264', 
            '-preset', 'medium',  # Balance between speed and quality
            '-crf', '23',         # Constant Rate Factor for quality
            '-c:a', 'aac',
            '-b:a', '128k',       # Reduced audio bitrate from 192k
            '-pix_fmt', 'yuv420p',
            '-t', str(total_duration),
            '-max_muxing_queue_size', '9999',  # Prevent muxing queue errors
            output_path
        ]
        
        print("Running FFmpeg command:")
        print(" ".join(cmd))
        
        try:
            # Run the FFmpeg command and capture output
            process = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check if the process was successful
            if process.returncode == 0:
                print(f"Video created successfully: {output_path}")
                return True
            else:
                print(f"Error creating video. FFmpeg output:")
                print(process.stderr)

        except Exception as e:
            print(f"Error creating video: {e}")
            return False

def get_part_of_description(description, max_length=1500):
    """
    Get a part of the description that fits within the max length.
    Cut off only at paragraph breaks. Remove first paragraph.
    """
    if len(description) <= max_length:
        return description
    
    # Split by paragraph breaks
    paragraphs = description.split('\n')[1:]  # Skip the first paragraph
    current_length = 0
    selected_paragraphs = []
    
    for paragraph in paragraphs:
        if current_length + len(paragraph) <= max_length:
            selected_paragraphs.append(paragraph)
            current_length += len(paragraph) + 1  # +1 for the newline character
        else:
            break
    
    return '\n'.join(selected_paragraphs)
    

def ffmpeg_availability_check():
    """Check if ffmpeg and ffprobe are available in the system."""
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE)
        subprocess.run(['ffprobe', '-version'], check=True, stdout=subprocess.PIPE)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("ERROR: ffmpeg or ffprobe not found. Please install FFmpeg and make sure it's in your system PATH.")
        return False
        

def process_castle_spreadsheet(csv_path, output_dir="castle_videos", start_index=0, jump=10):
    """
    Process a spreadsheet of castles to create TikTok-style videos.
    
    Parameters:
    - csv_path: Path to CSV with columns 'name', 'description', and 'image_urls' (as JSON string list)
    - output_dir: Directory to save videos
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create temp directory for images
    temp_dir = os.path.join(output_dir, "temp")
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Read castle data
    df = pd.read_csv(csv_path)[start_index:start_index+jump]
    
    for index, row in df.iterrows():
        try:
            castle_name = row['name']
            raw_description = row['description']
            description = get_part_of_description(raw_description, max_length=1300)            
            # Check url lists
            wikimedia_urls = row['wikimedia_image_urls']
            if not isinstance(wikimedia_urls, list):
                wikimedia_urls = literal_eval(wikimedia_urls)
            wikipedia_urls = row['wikipedia_image_urls']
            if not isinstance(wikipedia_urls, list):
                wikipedia_urls = literal_eval(wikipedia_urls)

            # Combine all image URLs
            image_urls = wikimedia_urls + wikipedia_urls
            print(f"\nProcessing castle {index+1}/{len(df)}: {castle_name}")
            print(f"Found {len(image_urls)} images for this castle")
            
            # Generate safe filename
            safe_name = "".join([c if c.isalnum() else "_" for c in castle_name])
            
            # Prepare file paths
            audio_path = os.path.join(output_dir, f"{safe_name}_audio.mp3")
            subtitle_path = os.path.join(output_dir, f"{safe_name}_subtitles.srt")
            video_path = os.path.join(output_dir, f"{safe_name}_video.mp4")
            
            # Step 1: Download all images
            image_paths = []
            for i, url in enumerate(image_urls):
                image_path = os.path.join(temp_dir, f"{safe_name}_image_{i}.jpg")
                print(f"Downloading image {i+1}/{len(image_urls)} for {castle_name}...")
                try:
                    if download_image(url, image_path):
                        image_paths.append(image_path)
                    else:
                        print(f"Failed to download image {i+1} - skipping this image")
                    
                except Exception as e:
                    print(f"Error downloading image {i+1}: {e}")            
            if not image_paths:
                print(f"No images could be downloaded for {castle_name} - skipping")
                continue

            # add input validation for images so they can be manually deleted if needed
            input_key = input(f"Downloaded {len(image_paths)} images for {castle_name}")
            # if escape key is pressed skip this castle
            if input_key == 'q':
                print(f"Skipping {castle_name} as per user request")
                for img_path in image_paths:
                    try:
                        os.remove(img_path)
                    except Exception as e:
                        print(f"Error deleting image {img_path}: {e}")
                continue
            
            # Step 2: Generate audio narration with synchronized subtitles
            print(f"Generating voiceover and subtitles for {castle_name}...")
            result = generate_azure_voice_with_subtitles(description, audio_path, subtitle_path)
            if not result[0]:
                print(f"Skipping {castle_name} due to voice/subtitle generation failure")
                continue

            # Step 3: Create video with multiple images and subtitles
            print(f"Creating video for {castle_name} with {len(image_paths)} images and subtitles...")
            # Use absolute path for subtitle file
            subtitle_path_abs = os.path.abspath(subtitle_path)
            print(f"Subtitle path for FFmpeg: {subtitle_path_abs}")
            
            create_castle_video(image_paths, audio_path, subtitle_path_abs, video_path, castle_name)
            
            print(f"Completed video for {castle_name}: {video_path}")

            # delete temporrary images after video creation and the srt and mp3 files
            for img_path in image_paths:
                try:
                    os.remove(img_path)
                except Exception as e:
                    print(f"Error deleting image {img_path}: {e}")

            try:
                os.remove(audio_path)
                os.remove(subtitle_path)
            except Exception as e:
                print(f"Error deleting audio/subtitle files: {e}")
            
            # Optional: add a small delay between API calls
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing {castle_name}: {e}")


# Main execution
if __name__ == "__main__":
    if ffmpeg_availability_check():
        # Process the castle spreadsheet
        process_castle_spreadsheet('outputs/final/only_castles_v4.csv', start_index=180, jump=10)