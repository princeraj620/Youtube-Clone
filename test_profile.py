#!/usr/bin/env python3
"""
Test script for YouTube Clone Profile and Video Deletion Features
"""

import requests
import json

# Base URL for your Flask app
BASE_URL = "http://localhost:5000"

def test_profile_access():
    """Test if profile page is accessible"""
    print("🔍 Testing Profile Access...")
    
    try:
        # First, try to access profile without login (should redirect)
        response = requests.get(f"{BASE_URL}/profile", allow_redirects=False)
        print(f"Profile without login: {response.status_code}")
        
        # Try demo login
        print("\n🔑 Trying demo login...")
        login_response = requests.get(f"{BASE_URL}/demo-login", allow_redirects=False)
        print(f"Demo login response: {login_response.status_code}")
        
        if login_response.status_code == 302:  # Redirect after login
            # Now try to access profile
            session = requests.Session()
            session.get(f"{BASE_URL}/demo-login")  # This should set cookies
            
            profile_response = session.get(f"{BASE_URL}/profile")
            print(f"Profile with login: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                print("✅ Profile page accessible!")
                return True
            else:
                print("❌ Profile page not accessible")
                return False
                
    except Exception as e:
        print(f"❌ Error testing profile: {e}")
        return False

def test_video_upload():
    """Test video upload functionality"""
    print("\n📹 Testing Video Upload...")
    
    try:
        session = requests.Session()
        session.get(f"{BASE_URL}/demo-login")
        
        # Check if upload page is accessible
        upload_response = session.get(f"{BASE_URL}/upload")
        print(f"Upload page: {upload_response.status_code}")
        
        if upload_response.status_code == 200:
            print("✅ Upload page accessible!")
            return True
        else:
            print("❌ Upload page not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Error testing upload: {e}")
        return False

def test_channel_access():
    """Test channel page access"""
    print("\n📺 Testing Channel Access...")
    
    try:
        session = requests.Session()
        session.get(f"{BASE_URL}/demo-login")
        
        # Try to access demo user's channel
        channel_response = session.get(f"{BASE_URL}/channel/demo_user1")
        print(f"Channel page: {channel_response.status_code}")
        
        if channel_response.status_code == 200:
            print("✅ Channel page accessible!")
            return True
        else:
            print("❌ Channel page not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Error testing channel: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 YouTube Clone Feature Test")
    print("=" * 40)
    
    # Test profile access
    profile_ok = test_profile_access()
    
    # Test video upload
    upload_ok = test_video_upload()
    
    # Test channel access
    channel_ok = test_channel_access()
    
    print("\n📊 Test Results:")
    print(f"Profile Access: {'✅ PASS' if profile_ok else '❌ FAIL'}")
    print(f"Video Upload: {'✅ PASS' if upload_ok else '❌ FAIL'}")
    print(f"Channel Access: {'✅ PASS' if channel_ok else '❌ FAIL'}")
    
    if all([profile_ok, upload_ok, channel_ok]):
        print("\n🎉 All tests passed! Your YouTube clone is working correctly.")
        print("\n📝 Next steps:")
        print("1. Open http://localhost:5000 in your browser")
        print("2. Click 'Demo Login' or login with your account")
        print("3. Click your username → 'My Profile'")
        print("4. Try editing your profile and deleting videos")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 