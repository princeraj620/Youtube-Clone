#!/usr/bin/env python3
"""
YouTube Clone Startup Script
This script ensures all dependencies are installed and starts the application
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages. Please check your internet connection.")
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'flask', 'pymongo', 'bcrypt', 'pillow', 'opencv-python', 
        'moviepy', 'flask-login', 'werkzeug'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'uploads/videos', 'uploads/thumbnails', 'static/img']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("📁 Directories created successfully!")

def main():
    print("🎉 Welcome to YouTube Clone!")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found. Please run this script from the project directory.")
        return
    
    # Create directories
    create_directories()
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("📦 Installing missing packages...")
        if not install_requirements():
            return
    else:
        print("✅ All dependencies are installed!")
    
    print("\n🚀 Starting YouTube Clone...")
    print("=" * 50)
    
    # Start the application
    try:
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 YouTube Clone stopped. Goodbye!")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main() 