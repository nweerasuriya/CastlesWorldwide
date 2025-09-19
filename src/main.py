# src/main.py - Main posting orchestrator (YouTube only)
import json
import os
from datetime import datetime
from src.youtube_uploader import YouTubeUploader

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
    print("🤖 Starting daily YouTube posting...")
    
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
    
    # Initialize YouTube uploader
    youtube_uploader = YouTubeUploader()
    if not youtube_uploader.service:
        print("❌ Failed to initialize YouTube uploader")
        return
    
    posted_count = 0
    
    for post in today_posts:
        print(f"\n🎬 Processing: {post['youtube']['title']}")
        
        # Check if video file exists
        if not os.path.exists(post['video_file']):
            print(f"❌ Video file not found: {post['video_file']}")
            continue
        
        # Upload to YouTube
        try:
            print("📺 Uploading to YouTube...")
            video_id = youtube_uploader.upload_video(
                video_path=post['video_file'],
                title=post['youtube']['title'],
                description=post['youtube']['description'],
                tags=post['youtube']['tags']
            )
            
            if video_id:
                print(f"✅ YouTube upload successful: https://youtube.com/watch?v={video_id}")
                post['posted'] = True
                post['posted_timestamp'] = datetime.now().isoformat()
                post['youtube_video_id'] = video_id
                posted_count += 1
            else:
                print("❌ YouTube upload failed")
        except Exception as e:
            print(f"❌ YouTube upload error: {e}")
    
    # Save updated schedule
    save_schedule(schedule)
    
    print(f"\n🎉 Daily posting complete! Posted {posted_count}/{len(today_posts)} videos to YouTube")

if __name__ == "__main__":
    main()

