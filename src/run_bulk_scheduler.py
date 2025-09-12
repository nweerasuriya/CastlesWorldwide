"""
Enter script name

Enter short description of the script
"""

__date__ = "2025-09-09"
__author__ = "NedeeshaWeerasuriya"
__version__ = "0.1"


from schedule_generator import get_castle_description, save_schedule_to_file
import os

def main():
    print("Castle Video Bulk Scheduler")
    print("=" * 40)
    
    # Get user input (with your defaults)
    start_date = input("Enter start date (DD/MM/YYYY HH:MM) [04/09/2025 17:00]: ") or "04/09/2025 17:00"
    video_dir = input("Enter video directory path [content/videos]: ") or "content/videos"
    frequency = int(input("Enter posting frequency (days) [1]: ") or "1")
    
    # Check if directory exists and has videos
    if not os.path.exists(video_dir):
        print(f"❌ Directory {video_dir} not found!")
        return
    
    castle_files = [f for f in os.listdir(video_dir) if f.endswith('_video.mp4')]
    if not castle_files:
        print(f"❌ No castle videos (*_video.mp4) found in {video_dir}")
        return
    
    print(f"\n📹 Found {len(castle_files)} castle videos:")
    for i, filename in enumerate(castle_files[:5], 1):  # Show first 5
        castle_name = filename.split('_video')[0].replace('_', ' ').title()
        print(f"  {i}. {castle_name}")
    if len(castle_files) > 5:
        print(f"  ... and {len(castle_files) - 5} more")
    
    # Generate schedule using your original logic
    print(f"\nGenerating schedule...")
    schedule = get_castle_description(
        start_date=start_date,
        video_directory=video_dir,
        freq=frequency
    )
    
    # Save schedule
    output_path = "content/schedule.json"
    save_schedule_to_file(schedule, output_path)
    
    print(f"✅ Generated {len(schedule['posts'])} castle posts")
    print(f"📅 Schedule saved to: {output_path}")
    
    # Show summary (like your original Excel output)
    if schedule['posts']:
        first_post = schedule['posts'][0]['scheduled_date']
        last_post = schedule['posts'][-1]['scheduled_date']
        print(f"📅 Posting range: {first_post} to {last_post}")
        print(f"🕐 Daily at 5:00 PM UK time")
    
    print(f"\n📋 Sample posts:")
    for i, post in enumerate(schedule['posts'][:2]):
        print(f"  {i+1}. {post['youtube']['title']}")
        print(f"     Date: {post['scheduled_date']}")
    

if __name__ == "__main__":
    main()