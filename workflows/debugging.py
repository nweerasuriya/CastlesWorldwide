
# %% --------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------


import os
import subprocess
import json

def check_video_specs(video_path):
    """Check if video meets Instagram requirements"""
    cmd = [
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        
        # Get video stream
        video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
        
        if video_stream:
            print(f"Codec: {video_stream.get('codec_name')}")
            print(f"Resolution: {video_stream.get('width')}x{video_stream.get('height')}")
            print(f"Duration: {float(data['format'].get('duration', 0)):.2f}s")
            print(f"File size: {int(data['format'].get('size', 0)) / 1024 / 1024:.2f}MB")
            
            # Check requirements
            if video_stream.get('codec_name') != 'h264':
                print("⚠️ WARNING: Should be H.264 codec")
            
            duration = float(data['format'].get('duration', 0))
            if duration < 3 or duration > 90:
                print(f"⚠️ WARNING: Duration should be 3-90s, got {duration:.2f}s")
                
    except Exception as e:
        print(f"Error checking video: {e}")

check_video_specs('C:/Users/nedee/Python_Projects/CastlesWorldwide/content/castle_videos/Castelo_de_Torres_Vedras_video.mp4')


# %% --------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------
import requests
import os
url = "https://raw.githubusercontent.com/nweerasuriya/CastlesWorldwide/main/content/castle_videos/Château_de_Lichtenberg_video.mp4"

response = requests.head(url, allow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Final URL: {response.url}")
print(f"Content-Type: {response.headers.get('content-type')}")
print(f"Content-Length: {int(response.headers.get('content-length', 0)) / 1024 / 1024:.2f} MB")
# %%
import requests
from io import BytesIO

# Download and check the actual video
url = "https://raw.githubusercontent.com/nweerasuriya/CastlesWorldwide/main/content/castle_videos/Ch%C3%A2teau_de_Lichtenberg_video.mp4"
response = requests.get(url)


# %%
from src.instagram_poster import InstagramPoster
import time
import requests
import os

instagram_poster = InstagramPoster()
instagram_poster.verify_token()

def post_video(video_path, caption):
    """Post video to Instagram as Reel using GitHub-hosted video"""
    
    try:
        video_url = video_path
        
        # Step 2: Create media container
        print("📤 Creating Instagram media container...")
        user_id = os.getenv('INSTAGRAM_USER_ID')

        create_url = f"https://graph.facebook.com/v21.0/{user_id}/media"

        params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption,
            'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN')
        }
        
        print(f"🎬 Posting video: {os.path.basename(video_path)}")
        print(f"📝 Caption: {caption[:50]}...")
        
        response = requests.post(create_url, data=params)
        response_data = response.json()
        
        if 'id' not in response_data:
            print(f"❌ Failed to create media container")
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            # Check for specific errors
            if 'error' in response_data:
                error_msg = response_data['error'].get('message', 'Unknown error')
                error_code = response_data['error'].get('code', 'Unknown code')
                print(f"❌ Instagram API Error ({error_code}): {error_msg}")
            
            return False
        
        container_id = response_data['id']
        print(f"✅ Media container created: {container_id}")
        
        # Step 3: Check container status and wait for processing
        print("⏳ Waiting for media processing...")
        max_attempts = 30  # Wait up to 10 minutes
        
        for attempt in range(max_attempts):
            status_url = f"https://graph.facebook.com/v21.0/{container_id}"
            status_params = {
                'fields': 'status_code',
                'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN')
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            status_data = status_response.json()
            
            status_code = status_data.get('status_code', 'UNKNOWN')
            print(f"🔄 Processing status: {status_code} (attempt {attempt + 1}/{max_attempts})")
            
            if status_code == 'FINISHED':
                print("✅ Media processing completed")
                break
            elif status_code == 'ERROR':
                print(f"❌ Media processing failed: {status_data}")
                return False
            elif status_code in ['IN_PROGRESS', 'PUBLISHED']:
                # Continue waiting
                time.sleep(10)  # Wait 10 seconds before checking again
            else:
                print(f"⚠️ Unknown status: {status_code}")
                time.sleep(10)
        else:
            print("❌ Media processing timeout (10 minutes)")
            return False
        
        # Step 4: Publish media
        print("📱 Publishing to Instagram...")
        publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': os.getenv('INSTAGRAM_ACCESS_TOKEN')
        }
        
        publish_response = requests.post(publish_url, data=publish_params, timeout=30)
        publish_data = publish_response.json()
        
        if 'id' in publish_data:
            media_id = publish_data['id']
            print(f"🎉 Successfully posted to Instagram!")
            print(f"📱 Media ID: {media_id}")
            return media_id
        else:
            print(f"❌ Failed to publish to Instagram")
            print(f"Response: {json.dumps(publish_data, indent=2)}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout - Instagram API might be slow")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Instagram posting error: {e}")
        return False
    

if instagram_poster.verify_token():
    # post video
    post_video(
        video_path='https://raw.githubusercontent.com/nweerasuriya/CastlesWorldwide/main/content/castle_videos/Castelo_de_Torres_Vedras_video.mp4',
        caption='🏰 Castelo De Torres Vedras #castles #castlesworldwide #CastleLovers #shorts'
    )
# %%
# Remove _video from filenames in a directory
import os
def rename_videos_in_directory(directory):
    for filename in os.listdir(directory):
        if '_video' in filename:
            new_filename = filename.replace('_video', '')
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_filename)
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} -> {new_filename}")

rename_videos_in_directory('holding_castle_videos')
# %%
