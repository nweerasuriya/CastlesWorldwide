# src/instagram_poster.py - Instagram posting functionality for GitHub-hosted videos
import requests
import os
import time
import json

class InstagramPoster:
    def __init__(self):
        self.access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
        self.user_id = os.getenv('INSTAGRAM_USER_ID')
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.access_token or not self.user_id:
            print("❌ Instagram credentials not found in environment variables")
            print("Required: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID")
    
    def get_github_video_url(self, video_path):
        """Convert local GitHub path to raw GitHub URL"""
        try:
            # Get repository info from environment
            repo = os.environ.get('GITHUB_REPOSITORY')  # e.g., "nweerasuriya/CastlesWorldwide"
            
            if not repo:
                print("❌ GITHUB_REPOSITORY not found in environment")
                return None
            
            # Convert path to raw GitHub URL
            
            github_url = f"https://raw.githubusercontent.com/{repo}/main/{video_path}"
            print(f"📡 GitHub video URL: {github_url}")
            
            # Test if URL is accessible
            test_response = requests.head(github_url, timeout=10)
            if test_response.status_code == 200:
                print("✅ Video URL is accessible")
                return github_url
            else:
                print(f"❌ Video URL not accessible: {test_response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating GitHub URL: {e}")
            return None
    
    def post_video(self, video_path, caption):
        """Post video to Instagram as Reel using GitHub-hosted video"""
        if not self.access_token or not self.user_id:
            print("❌ Instagram credentials missing")
            return False
        
        try:
            # Step 1: Get GitHub URL for video
            video_url = self.get_github_video_url(video_path)
            if not video_url:
                return False
            
            # Step 2: Create media container
            print("📤 Creating Instagram media container...")
            
            create_url = f"{self.base_url}/{self.user_id}/media"
            
            params = {
                'media_type': 'REELS',
                'video_url': video_url,
                'caption': caption,
                'access_token': self.access_token
            }
            
            print(f"🎬 Posting video: {os.path.basename(video_path)}")
            print(f"📝 Caption: {caption[:50]}...")
            
            response = requests.post(create_url, data=params, timeout=30)
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
            max_attempts = 60  # Wait up to 10 minutes
            
            for attempt in range(max_attempts):
                status_url = f"{self.base_url}/{container_id}"
                status_params = {
                    'fields': 'status_code',
                    'access_token': self.access_token
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
            publish_url = f"{self.base_url}/{self.user_id}/media_publish"
            publish_params = {
                'creation_id': container_id,
                'access_token': self.access_token
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
    
    def test_credentials(self):
        """Test if Instagram credentials are working"""
        if not self.access_token or not self.user_id:
            return False
        
        try:
            url = f"{self.base_url}/{self.user_id}"
            params = {
                'fields': 'id,username',
                'access_token': self.access_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Instagram credentials valid for user: {data.get('username', 'Unknown')}")
                return True
            else:
                print(f"❌ Instagram credentials invalid: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing Instagram credentials: {e}")
            return False

# Test script to verify Instagram setup
if __name__ == "__main__":
    print("🧪 Instagram Poster Test")
    print("=" * 30)
    
    # Test credentials
    poster = InstagramPoster()
    
    if poster.test_credentials():
        print("\n✅ Instagram setup is working!")
        
        # Test URL generation
        test_video = "content/castles_videos/test_video.mp4"
        test_url = poster.get_github_video_url(test_video)
        
        if test_url:
            print(f"✅ GitHub URL generation working: {test_url}")
        else:
            print("❌ GitHub URL generation failed")
    else:
        print("\n❌ Instagram setup has issues")
        print("Check your environment variables:")
        print("- INSTAGRAM_ACCESS_TOKEN")
        print("- INSTAGRAM_USER_ID")