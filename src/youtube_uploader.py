from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

class YouTubeUploader:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with YouTube API using OAuth credentials"""
        try:
            # Get credentials from environment variables
            refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
            client_id = os.environ.get("YOUTUBE_CLIENT_ID")
            client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
            
            if not all([refresh_token, client_id, client_secret]):
                print("❌ Missing YouTube OAuth credentials in environment variables")
                print("Required: YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET")
                return False
            
            # Create credentials object
            creds = Credentials(
                None,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token"
            )
            
            # Build YouTube service
            self.service = build("youtube", "v3", credentials=creds)
            print("✅ YouTube authentication successful")
            return True
            
        except Exception as e:
            print(f"❌ YouTube authentication failed: {e}")
            return False
    
    def upload_video(self, video_path, title, description, tags):
        """Upload video to YouTube"""
        if not self.service:
            print("❌ YouTube service not authenticated")
            return None
        
        try:
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22',  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'public',  # Change to 'private' or 'unlisted' if needed
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            print(f"📤 Starting upload of {os.path.basename(video_path)}...")
            
            # Execute upload
            insert_request = self.service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = insert_request.execute()
            
            if 'id' in response:
                video_id = response['id']
                print(f"✅ Upload completed successfully")
                return video_id
            else:
                print("❌ Upload failed: No video ID returned")
                return None
                
        except Exception as e:
            print(f"❌ YouTube upload error: {e}")
            return None