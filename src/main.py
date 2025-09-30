# src/main.py - Main posting orchestrator (YouTube + Instagram)
import json
import os
from datetime import datetime
from youtube_uploader import YouTubeUploader
from instagram_poster import InstagramPoster

def load_schedule():
    """Load the posting schedule from JSON file"""
    try:
        with open('content/schedule.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No schedule.json found. Run the bulk scheduler first.")
        return None
    except json.JSONDecodeError:
        print("❌ Invalid JSON in schedule.json")
        return None

def save_schedule(schedule_data):
    """Save updated schedule back to JSON file"""
    with open('content/schedule.json', 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, indent=2, ensure_ascii=False)

def get_today_posts(schedule_data):
    """Get posts scheduled for today"""
    today = datetime.now().strftime('%Y-%m-%d')
    today_posts = []
    
    for post in schedule_data.get('posts', []):
        if post['scheduled_date'] == today and not post['posted']:
            today_posts.append(post)
    
    return today_posts

def main():
    print("🤖 Starting daily social media posting...")
    print("🎯 Platforms: YouTube + Instagram")
    
    # Load schedule
    schedule = load_schedule()
    if not schedule:
        return
    
    # Get today's posts
    today_posts = get_today_posts(schedule)
    if not today_posts:
        print("📅 No posts scheduled for today")
        return
    
    print(f"📋 Found {len(today_posts)} posts scheduled for today")
    
    # Initialize uploaders
    youtube_uploader = YouTubeUploader()
    instagram_poster = InstagramPoster()
    
    # Test credentials first
    youtube_ready = youtube_uploader.service is not None
    instagram_ready = instagram_poster.test_instagram_basic_credentials()
    
    print(f"📺 YouTube: {'✅ Ready' if youtube_ready else '❌ Not Ready'}")
    print(f"📱 Instagram: {'✅ Ready' if instagram_ready else '❌ Not Ready'}")
    
    if not (youtube_ready or instagram_ready):
        print("❌ No platforms available - check your credentials")
        return
    
    posted_count = 0
    
    for post in today_posts:
        print(f"{'='*60}")
        print(f"🎬 Processing: {post['youtube']['title']}")
        print(f"📁 Video: {post['video_file']}")
        
        # Check if video file exists
        if not os.path.exists(post['video_file']):
            print(f"❌ Video file not found: {post['video_file']}")
            continue
        
        youtube_success = False
        instagram_success = False
        
        # Upload to YouTube
        if youtube_ready:
            try:
                print(f"📺 YOUTUBE UPLOAD")
                print("-" * 20)
                video_id = youtube_uploader.upload_video(
                    video_path=post['video_file'],
                    title=post['youtube']['title'],
                    description=post['youtube']['description'],
                    tags=post['youtube']['tags']
                )
                
                if video_id:
                    print(f"✅ YouTube: https://youtube.com/watch?v={video_id}")
                    post['youtube_video_id'] = video_id
                    youtube_success = True
                else:
                    print("❌ YouTube upload failed")
            except Exception as e:
                print(f"❌ YouTube upload error: {e}")
        else:
            print("⏭️ Skipping YouTube (credentials not available)")
        
        # Post to Instagram
        if instagram_ready:
            try:
                print(f"📱 INSTAGRAM UPLOAD")
                print("-" * 22)
                media_id = instagram_poster.post_video(
                    video_path=post['video_file'],
                    caption=post['instagram']['caption']
                )
                
                if media_id:
                    print(f"✅ Instagram: Media ID {media_id}")
                    post['instagram_media_id'] = media_id
                    instagram_success = True
                else:
                    print("❌ Instagram upload failed")
            except Exception as e:
                print(f"❌ Instagram upload error: {e}")
        else:
            print("⏭️ Skipping Instagram (credentials not available)")
        
        # Mark as posted if at least one platform succeeded
        if youtube_success or instagram_success:
            post['posted'] = True
            post['posted_timestamp'] = datetime.now().isoformat()
            post['platforms_posted'] = {
                'youtube': youtube_success,
                'instagram': instagram_success
            }
            posted_count += 1
            
            success_platforms = []
            if youtube_success: success_platforms.append("YouTube")
            if instagram_success: success_platforms.append("Instagram")
            
            print(f"🎉 SUCCESS: Posted to {' + '.join(success_platforms)}")
        else:
            print(f"💥 FAILED: No platforms succeeded")
    
    # Save updated schedule
    save_schedule(schedule)
    
    print(f"🏁 DAILY POSTING COMPLETE!")
    print(f"📊 Posted {posted_count}/{len(today_posts)} items")
    print(f"🕐 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()