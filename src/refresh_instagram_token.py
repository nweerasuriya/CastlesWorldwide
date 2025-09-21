import requests
import os
import subprocess
import json

def refresh_and_update_token():
    """Simple token refresh using GitHub CLI"""
    
    current_token = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
    
    if not current_token:
        print("❌ No current Instagram token found")
        return False
    
    try:
        # Refresh the token
        url = "https://graph.instagram.com/refresh_access_token"
        params = {
            'grant_type': 'ig_refresh_token',
            'access_token': current_token
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            new_token = data.get('access_token')
            
            if new_token:
                print("✅ Token refreshed successfully")
                
                # Use GitHub CLI to update secret
                result = subprocess.run([
                    'gh', 'secret', 'set', 'INSTAGRAM_ACCESS_TOKEN',
                    '--body', new_token
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ GitHub secret updated")
                    return True
                else:
                    print(f"❌ Failed to update secret: {result.stderr}")
                    return False
            else:
                print("❌ No new token received")
                return False
        else:
            print(f"❌ Refresh failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    refresh_and_update_token()