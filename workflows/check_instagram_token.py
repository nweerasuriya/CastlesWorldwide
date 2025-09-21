# check_instagram_token.py - Check your current Instagram token details
import requests
from datetime import datetime, timedelta

def check_instagram_token(access_token):
    """Check Instagram token validity and expiry"""
    
    try:
        # Check token info using Instagram Graph API
        url = "https://graph.instagram.com/me"
        params = {
            'fields': 'id,username',
            'access_token': access_token
        }
        
        print("🔍 Checking Instagram token...")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token is valid!")
            print(f"👤 Connected to: {user_data.get('username', 'Unknown')}")
            print(f"🆔 User ID: {user_data.get('id', 'Unknown')}")
            
            # Check token expiry using debug endpoint
            debug_url = "https://graph.facebook.com/debug_token"
            debug_params = {
                'input_token': access_token,
                'access_token': access_token  # Self-debug
            }
            
            debug_response = requests.get(debug_url, params=debug_params)
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                token_info = debug_data.get('data', {})
                
                # Check if it's long-lived
                expires_at = token_info.get('expires_at')
                if expires_at:
                    expiry_date = datetime.fromtimestamp(expires_at)
                    days_remaining = (expiry_date - datetime.now()).days
                    
                    print(f"📅 Token expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"⏰ Days remaining: {days_remaining}")
                    
                    if days_remaining > 50:
                        print("✅ Long-lived token (60 days) - Good!")
                    elif days_remaining > 0:
                        print("⚠️  Token expires soon - should refresh")
                    else:
                        print("❌ Token has expired")
                else:
                    print("🔄 Short-lived token (1 hour) - needs to be exchanged for long-lived")
                
                # Check scopes
                scopes = token_info.get('scopes', [])
                print(f"🔐 Token scopes: {', '.join(scopes)}")
                
                return True
            else:
                print("⚠️  Could not get token debug info")
                return True  # Token works, just can't get expiry
                
        else:
            print(f"❌ Token is invalid or expired")
            print(f"Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking token: {e}")
        return False

def exchange_for_long_lived_token(short_token, app_id, app_secret):
    """Exchange short-lived token for long-lived token (if needed)"""
    
    try:
        url = "https://graph.facebook.com/v18.0/oauth/access_token"
        params = {
            'grant_type': 'ig_exchange_token',
            'client_id': app_id,
            'client_secret': app_secret,
            'ig_access_token': short_token
        }
        
        print("🔄 Exchanging for long-lived token...")
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            long_token = data.get('access_token')
            expires_in = data.get('expires_in', 5184000)  # Default 60 days
            
            print(f"✅ Long-lived token obtained!")
            print(f"⏰ Valid for {expires_in // 86400} days")
            print(f"🔑 New token: {long_token}")
            
            return long_token
        else:
            print(f"❌ Failed to exchange token: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error exchanging token: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Instagram Token Checker")
    print("=" * 30)
    
    # Get your current token
    token = input("Enter your Instagram access token: ").strip()
    
    if not token:
        print("❌ No token provided")
        exit(1)
    
    # Check the token
    is_valid = check_instagram_token(token)
    
    if not is_valid:
        print("\n💡 If you have a short-lived token, you can exchange it:")
        exchange = input("Do you want to exchange for long-lived token? (y/n): ").lower()
        
        if exchange == 'y':
            app_id = input("Enter your Facebook App ID: ").strip()
            app_secret = input("Enter your Facebook App Secret: ").strip()
            
            if app_id and app_secret:
                long_token = exchange_for_long_lived_token(token, app_id, app_secret)
                if long_token:
                    print("\n✅ Use this long-lived token in your GitHub secrets!")
            else:
                print("❌ App ID and Secret required for exchange")
    
    print("\n📝 Next steps:")
    print("1. If you have a valid long-lived token, add it to GitHub Secrets")
    print("2. Set up the token refresh automation")
    print("3. Your Instagram posting will work for 60 days automatically!")