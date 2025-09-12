import pandas as pd
import json
import os
from datetime import datetime, timedelta

def create_date_range(start_date, end_date, freq='1D'):
    """Create date range with specified frequency - same as your original logic"""
    start_date = pd.to_datetime(start_date, format="%d/%m/%Y %H:%M")
    end_date = pd.to_datetime(end_date, format="%d/%m/%Y %H:%M")
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    # create d/m/y H:M format
    return date_range.strftime("%d/%m/%Y %H:%M").tolist()

def get_castle_names_from_videos(directory):
    """Extract castle names from directory - same as your original logic"""
    castle_names = []
    for filename in os.listdir(directory):
        if filename.endswith("_video.mp4"):
            castle_name = filename.split('_video')[0]
            castle_names.append({
                'name': castle_name,
                'filename': filename
            })
    return castle_names

def get_castle_description(start_date, video_directory, freq=1):
    """Generate castle posting schedule - adapted from your original logic"""
    castle_data = get_castle_names_from_videos(video_directory)
    castle_df = pd.DataFrame(castle_data)
    
    total_days_needed = len(castle_df) * freq
    # calculate the end date based on the start date and total days needed
    end_date = pd.to_datetime(start_date, format='%d/%m/%Y %H:%M') + pd.Timedelta(days=total_days_needed)
    # create the new date range with the updated end date
    date_range = create_date_range(start_date, end_date.strftime('%d/%m/%Y %H:%M'), freq=f"{freq}D")
    
    castle_df['date'] = date_range[:-1]
    hashtags = "#castles #castlesworldwide #CastleLovers #shorts"
    
    # Create the posts list for JSON
    posts = []
    for i, row in castle_df.iterrows():
        # Convert date to ISO format for easier processing
        scheduled_date = pd.to_datetime(row['date'], format='%d/%m/%Y %H:%M').strftime('%Y-%m-%d')
        
        # Create post object
        post = {
            "id": f"castle_{i+1:03d}",
            "video_file": f"content/videos/{row['filename']}",
            "youtube": {
                "title": f"{row['name'].replace('_', ' ').title()} {hashtags}",
                "description": f"Explore the magnificent {row['name'].replace('_', ' ')} castle! {hashtags}",
                "tags": ["castles", "castlesworldwide", "CastleLovers", "shorts", "history", "architecture"]
            },
            "instagram": {
                "caption": f"🏰 {row['name'].replace('_', ' ').title()} {hashtags} ✨"
            },
            "scheduled_date": scheduled_date,
            "posted": False
        }
        posts.append(post)
    
    return {"posts": posts}

def save_schedule_to_file(schedule_data, output_path):
    """Save schedule data to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, indent=2, ensure_ascii=False)

# Main execution for bulk scheduling - same as your original approach
if __name__ == "__main__":
    # Your original configuration
    START_DATE = "04/09/2025 17:00"
    VIDEO_DIRECTORY = "content/videos"  # Changed from your "castle_videos/"
    OUTPUT_PATH = "content/schedule.json"
    FREQUENCY_DAYS = 1  # Same as your freq=1
    
    # Generate schedule using your logic
    schedule = get_castle_description(
        start_date=START_DATE,
        video_directory=VIDEO_DIRECTORY,
        freq=FREQUENCY_DAYS
    )
    
    # Save to file
    save_schedule_to_file(schedule, OUTPUT_PATH)
    
    print(f"Generated schedule with {len(schedule['posts'])} castle posts")
    print(f"Schedule saved to: {OUTPUT_PATH}")
    
    # Print first few posts for verification
    for i, post in enumerate(schedule['posts'][:3]):
        print(f"\nCastle Post {i+1}:")
        print(f"  Date: {post['scheduled_date']}")
        print(f"  Castle: {post['youtube']['title']}")
        print(f"  Video: {post['video_file']}")