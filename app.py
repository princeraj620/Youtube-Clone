from flask import Flask, render_template, request, redirect, url_for, Response, jsonify, flash, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datetime import datetime, timedelta
import os
import uuid
import json
import bcrypt
from bson import ObjectId
import cv2
from PIL import Image
import io
import base64
from moviepy.editor import VideoFileClip
import threading
import time

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# MongoDB configuration
client = MongoClient("mongodb+srv://mehernimra064:shahzadi123456789@cluster0.mgo1zg0.mongodb.net/")
db = client["youtube_clone"]
users_collection = db["users"]
videos_collection = db["videos"]
comments_collection = db["comments"]
likes_collection = db["likes"]
views_collection = db["views"]

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# File upload configuration
UPLOAD_FOLDER = 'uploads'
VIDEO_FOLDER = 'uploads/videos'
THUMBNAIL_FOLDER = 'uploads/thumbnails'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VIDEO_FOLDER'] = VIDEO_FOLDER
app.config['THUMBNAIL_FOLDER'] = THUMBNAIL_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Create upload directories if they don't exist
os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(THUMBNAIL_FOLDER, exist_ok=True)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.avatar = user_data.get('avatar', 'default-avatar.png')
        self.subscribers = user_data.get('subscribers', 0)
        self.subscribed_to = user_data.get('subscribed_to', [])

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_thumbnail(video_path, thumbnail_path):
    """Generate thumbnail from video"""
    try:
        clip = VideoFileClip(video_path)
        # Take frame at 1 second
        frame = clip.get_frame(1)
        clip.close()
        
        # Convert to PIL Image and save
        img = Image.fromarray(frame)
        img.save(thumbnail_path, 'JPEG')
        return True
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return False

def create_sample_data():
    """Create sample users and videos for demonstration"""
    try:
        # Check if sample data already exists
        if users_collection.count_documents({}) > 0:
            print("Sample data already exists, skipping...")
            return
        
        print("Creating sample data...")
        
        # Create sample users
        sample_users = [
            {
                'username': 'demo_user1',
                'email': 'demo1@example.com',
                'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()),
                'created_at': datetime.now() - timedelta(days=30),
                'subscribers': [],
                'subscribed_to': []
            },
            {
                'username': 'demo_user2',
                'email': 'demo2@example.com',
                'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()),
                'created_at': datetime.now() - timedelta(days=25),
                'subscribers': [],
                'subscribed_to': []
            },
            {
                'username': 'tech_channel',
                'email': 'tech@example.com',
                'password': bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()),
                'created_at': datetime.now() - timedelta(days=20),
                'subscribers': [],
                'subscribed_to': []
            }
        ]
        
        user_ids = []
        for user_data in sample_users:
            result = users_collection.insert_one(user_data)
            user_ids.append(result.inserted_id)
        
        # Create sample videos
        sample_videos = [
            {
                'title': 'Amazing Nature Documentary',
                'description': 'Explore the wonders of nature in this breathtaking documentary showcasing wildlife and landscapes.',
                'filename': 'sample_video_1.mp4',
                'thumbnail': '/static/img/default-thumbnail.jpg',
                'user_id': user_ids[0],
                'created_at': datetime.now() - timedelta(days=5),
                'views': 1250,
                'likes': 89,
                'dislikes': 3
            },
            {
                'title': 'Cooking Tutorial: Pasta Carbonara',
                'description': 'Learn how to make authentic Italian pasta carbonara with this step-by-step tutorial.',
                'filename': 'sample_video_2.mp4',
                'thumbnail': '/static/img/default-thumbnail.jpg',
                'user_id': user_ids[1],
                'created_at': datetime.now() - timedelta(days=3),
                'views': 890,
                'likes': 67,
                'dislikes': 1
            },
            {
                'title': 'Python Programming Basics',
                'description': 'Complete beginner guide to Python programming language with practical examples.',
                'filename': 'sample_video_3.mp4',
                'thumbnail': '/static/img/default-thumbnail.jpg',
                'user_id': user_ids[2],
                'created_at': datetime.now() - timedelta(days=1),
                'views': 2100,
                'likes': 156,
                'dislikes': 8
            },
            {
                'title': 'Guitar Lessons for Beginners',
                'description': 'Start your guitar journey with these essential beginner lessons and techniques.',
                'filename': 'sample_video_4.mp4',
                'thumbnail': '/static/img/default-thumbnail.jpg',
                'user_id': user_ids[0],
                'created_at': datetime.now() - timedelta(hours=12),
                'views': 750,
                'likes': 45,
                'dislikes': 2
            },
            {
                'title': 'Travel Vlog: Paris Adventure',
                'description': 'Join us on an amazing journey through the beautiful streets of Paris, France.',
                'filename': 'sample_video_5.mp4',
                'thumbnail': '/static/img/default-thumbnail.jpg',
                'user_id': user_ids[1],
                'created_at': datetime.now() - timedelta(hours=6),
                'views': 3200,
                'likes': 234,
                'dislikes': 12
            },
            {
                'title': 'Fitness Workout at Home',
                'description': 'Complete home workout routine that you can do anywhere without equipment.',
                'filename': 'sample_video_6.mp4',
                'thumbnail': '/static/img/default-thumbnail.jpg',
                'user_id': user_ids[2],
                'created_at': datetime.now() - timedelta(hours=2),
                'views': 1800,
                'likes': 123,
                'dislikes': 5
            }
        ]
        
        for video_data in sample_videos:
            videos_collection.insert_one(video_data)
        
        # Create sample comments
        sample_comments = [
            {
                'video_id': videos_collection.find_one({'title': 'Amazing Nature Documentary'})['_id'],
                'user_id': user_ids[1],
                'content': 'This is absolutely stunning! Great work!',
                'created_at': datetime.now() - timedelta(days=4)
            },
            {
                'video_id': videos_collection.find_one({'title': 'Cooking Tutorial: Pasta Carbonara'})['_id'],
                'user_id': user_ids[0],
                'content': 'I tried this recipe and it turned out amazing! Thank you!',
                'created_at': datetime.now() - timedelta(days=2)
            },
            {
                'video_id': videos_collection.find_one({'title': 'Python Programming Basics'})['_id'],
                'user_id': user_ids[1],
                'content': 'Very clear explanation. Perfect for beginners!',
                'created_at': datetime.now() - timedelta(hours=18)
            }
        ]
        
        for comment_data in sample_comments:
            comments_collection.insert_one(comment_data)
        
        # Create sample views
        for video in videos_collection.find():
            for i in range(video['views']):
                views_collection.insert_one({
                    'video_id': video['_id'],
                    'user_id': user_ids[i % len(user_ids)],
                    'viewed_at': video['created_at'] + timedelta(hours=i)
                })
        
        print("Sample data created successfully!")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")

@app.route('/')
def index():
    """Home page with trending videos"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Get trending videos (most viewed in last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    pipeline = [
        {
            '$lookup': {
                'from': 'views',
                'localField': '_id',
                'foreignField': 'video_id',
                'as': 'views'
            }
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'user'
            }
        },
        {
            '$addFields': {
                'view_count': {'$size': '$views'},
                'user_info': {'$arrayElemAt': ['$user', 0]}
            }
        },
        {
            '$sort': {'view_count': -1, 'created_at': -1}
        },
        {
            '$skip': (page - 1) * per_page
        },
        {
            '$limit': per_page
        }
    ]
    
    videos = list(videos_collection.aggregate(pipeline))
    
    return render_template('index.html', videos=videos, page=page)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if users_collection.find_one({'$or': [{'username': username}, {'email': email}]}):
            flash('Username or email already exists!', 'error')
            return render_template('register.html')
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Create user
        user_data = {
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.now(),
            'subscribers': 0,
            'subscribed_to': []
        }
        
        users_collection.insert_one(user_data)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user_data = users_collection.find_one({'username': username})
        
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password']):
            user = User(user_data)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file selected!', 'error')
            return render_template('upload.html')
        
        video_file = request.files['video']
        title = request.form['title']
        description = request.form['description']
        
        if video_file.filename == '':
            flash('No video file selected!', 'error')
            return render_template('upload.html')
        
        if video_file and allowed_file(video_file.filename):
            # Generate unique filename
            filename = secure_filename(video_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"
            video_path = os.path.join(app.config['VIDEO_FOLDER'], unique_filename)
            
            # Save video
            video_file.save(video_path)
            
            # Generate thumbnail
            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(app.config['THUMBNAIL_FOLDER'], thumbnail_filename)
            
            if generate_thumbnail(video_path, thumbnail_path):
                thumbnail_url = f"/thumbnails/{thumbnail_filename}"
            else:
                thumbnail_url = "/static/img/default-thumbnail.jpg"
            
            # Save video data to database
            video_data = {
                'title': title,
                'description': description,
                'filename': unique_filename,
                'thumbnail': thumbnail_url,
                'user_id': ObjectId(current_user.id),
                'created_at': datetime.now(),
                'views': 0,
                'likes': 0,
                'dislikes': 0
            }
            
            videos_collection.insert_one(video_data)
            flash('Video uploaded successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type!', 'error')
    
    return render_template('upload.html')

@app.route('/video/<video_id>')
def video(video_id):
    """Video watch page"""
    try:
        video_obj = videos_collection.find_one({'_id': ObjectId(video_id)})
        if not video_obj:
            flash('Video not found!', 'error')
            return redirect(url_for('index'))
        
        # Get user info
        user_data = users_collection.find_one({'_id': video_obj['user_id']})
        
        # Get comments
        comments = list(comments_collection.find({'video_id': ObjectId(video_id)}).sort('created_at', -1))
        
        # Get comment authors
        for comment in comments:
            comment_user = users_collection.find_one({'_id': comment['user_id']})
            comment['author'] = comment_user['username'] if comment_user else 'Unknown'
        
        # Increment view count
        if current_user.is_authenticated:
            views_collection.update_one(
                {'video_id': ObjectId(video_id), 'user_id': ObjectId(current_user.id)},
                {'$set': {'viewed_at': datetime.now()}},
                upsert=True
            )
        
        # Get related videos
        related_videos = list(videos_collection.find({
            'user_id': video_obj['user_id'],
            '_id': {'$ne': ObjectId(video_id)}
        }).limit(6))
        
        return render_template('video.html', 
                             video=video_obj, 
                             user=user_data, 
                             comments=comments,
                             related_videos=related_videos)
    
    except Exception as e:
        flash('Error loading video!', 'error')
        return redirect(url_for('index'))

@app.route('/videos/<filename>')
def serve_video(filename):
    """Serve video files"""
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def serve_thumbnail(filename):
    """Serve thumbnail files"""
    return send_from_directory(app.config['THUMBNAIL_FOLDER'], filename)

@app.route('/comment', methods=['POST'])
@login_required
def add_comment():
    video_id = request.form['video_id']
    content = request.form['content']
    
    if content.strip():
        comment_data = {
            'video_id': ObjectId(video_id),
            'user_id': ObjectId(current_user.id),
            'content': content,
            'created_at': datetime.now()
        }
        
        comments_collection.insert_one(comment_data)
        flash('Comment added successfully!', 'success')
    
    return redirect(url_for('video', video_id=video_id))

@app.route('/like/<video_id>', methods=['POST'])
@login_required
def like_video(video_id):
    """Like or unlike a video"""
    like_type = request.form.get('type', 'like')  # 'like' or 'dislike'
    
    # Check if user already liked/disliked
    existing_like = likes_collection.find_one({
        'video_id': ObjectId(video_id),
        'user_id': ObjectId(current_user.id)
    })
    
    if existing_like:
        if existing_like['type'] == like_type:
            # Remove like/dislike
            likes_collection.delete_one({'_id': existing_like['_id']})
            videos_collection.update_one(
                {'_id': ObjectId(video_id)},
                {'$inc': {f'{like_type}s': -1}}
            )
        else:
            # Change like type
            likes_collection.update_one(
                {'_id': existing_like['_id']},
                {'$set': {'type': like_type}}
            )
            videos_collection.update_one(
                {'_id': ObjectId(video_id)},
                {'$inc': {f'{like_type}s': 1, f'{existing_like["type"]}s': -1}}
            )
    else:
        # Add new like/dislike
        like_data = {
            'video_id': ObjectId(video_id),
            'user_id': ObjectId(current_user.id),
            'type': like_type,
            'created_at': datetime.now()
        }
        likes_collection.insert_one(like_data)
        videos_collection.update_one(
            {'_id': ObjectId(video_id)},
            {'$inc': {f'{like_type}s': 1}}
        )
    
    return jsonify({'success': True})

@app.route('/search')
def search():
    """Search videos"""
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))
    
    # Search in title and description
    videos = list(videos_collection.find({
        '$or': [
            {'title': {'$regex': query, '$options': 'i'}},
            {'description': {'$regex': query, '$options': 'i'}}
        ]
    }).sort('created_at', -1))
    
    return render_template('search.html', videos=videos, query=query)

@app.route('/channel/<username>')
def channel(username):
    """User channel page"""
    user_data = users_collection.find_one({'username': username})
    if not user_data:
        flash('Channel not found!', 'error')
        return redirect(url_for('index'))
    
    # Get user's videos
    videos = list(videos_collection.find({'user_id': user_data['_id']}).sort('created_at', -1))
    
    # Add user info to videos for display
    for video in videos:
        video['user_info'] = user_data
    
    # Check if current user is subscribed - handle subscribers field properly
    is_subscribed = False
    if current_user.is_authenticated:
        current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
        subscribers = user_data.get('subscribers', [])
        if isinstance(subscribers, list):
            is_subscribed = current_user.id in subscribers
        else:
            # If subscribers is not a list, assume not subscribed
            is_subscribed = False
    
    return render_template('channel.html', 
                         channel_user=user_data, 
                         videos=videos,
                         is_subscribed=is_subscribed)

@app.route('/subscribe/<user_id>', methods=['POST'])
@login_required
def subscribe(user_id):
    """Subscribe/unsubscribe to a channel"""
    target_user = users_collection.find_one({'_id': ObjectId(user_id)})
    if not target_user:
        return jsonify({'success': False, 'error': 'User not found'})
    
    current_user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    
    # Ensure subscribers field is a list
    subscribers = target_user.get('subscribers', [])
    if not isinstance(subscribers, list):
        subscribers = []
    
    if current_user.id in subscribers:
        # Unsubscribe
        subscribers.remove(current_user.id)
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'subscribers': subscribers}}
        )
        
        # Also remove from current user's subscribed_to list
        subscribed_to = current_user_data.get('subscribed_to', [])
        if isinstance(subscribed_to, list) and user_id in subscribed_to:
            subscribed_to.remove(user_id)
            users_collection.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'subscribed_to': subscribed_to}}
            )
        
        is_subscribed = False
    else:
        # Subscribe
        subscribers.append(current_user.id)
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'subscribers': subscribers}}
        )
        
        # Also add to current user's subscribed_to list
        subscribed_to = current_user_data.get('subscribed_to', [])
        if not isinstance(subscribed_to, list):
            subscribed_to = []
        if user_id not in subscribed_to:
            subscribed_to.append(user_id)
            users_collection.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'subscribed_to': subscribed_to}}
            )
        
        is_subscribed = True
    
    return jsonify({'success': True, 'is_subscribed': is_subscribed})

@app.route('/trending')
def trending():
    """Trending videos page"""
    # Get videos with most views in last 24 hours
    yesterday = datetime.now() - timedelta(days=1)
    
    pipeline = [
        {
            '$lookup': {
                'from': 'views',
                'localField': '_id',
                'foreignField': 'video_id',
                'as': 'views'
            }
        },
        {
            '$lookup': {
                'from': 'users',
                'localField': 'user_id',
                'foreignField': '_id',
                'as': 'user'
            }
        },
        {
            '$addFields': {
                'view_count': {'$size': '$views'},
                'user_info': {'$arrayElemAt': ['$user', 0]}
            }
        },
        {
            '$match': {
                'created_at': {'$gte': yesterday}
            }
        },
        {
            '$sort': {'view_count': -1}
        },
        {
            '$limit': 20
        }
    ]
    
    videos = list(videos_collection.aggregate(pipeline))
    return render_template('trending.html', videos=videos)

@app.route('/demo-login')
def demo_login():
    """Quick demo login for testing"""
    user_data = users_collection.find_one({'username': 'demo_user1'})
    if user_data:
        user = User(user_data)
        login_user(user)
        flash('Demo login successful! Welcome demo_user1', 'success')
    else:
        flash('Demo user not found. Please register first.', 'error')
    return redirect(url_for('index'))

@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    data = request.get_json()
    update_fields = {
        'username': data.get('username'),
        'email': data.get('email'),
        'phone': data.get('phone'),
        'location': data.get('location'),
        'website': data.get('website'),
        'bio': data.get('bio')
    }
    # Remove empty fields
    update_fields = {k: v for k, v in update_fields.items() if v is not None}
    users_collection.update_one({'_id': ObjectId(current_user.id)}, {'$set': update_fields})
    return jsonify({'success': True})

@app.route('/video/<video_id>/delete', methods=['POST'])
@login_required
def delete_video(video_id):
    """Delete a video (only by the video owner)"""
    video = videos_collection.find_one({'_id': ObjectId(video_id)})
    if not video:
        return jsonify({'success': False, 'message': 'Video not found'}), 404
    
    # Check if current user owns the video
    if str(video['user_id']) != str(current_user.id):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Delete video file
    video_path = os.path.join(VIDEO_FOLDER, video['filename'])
    if os.path.exists(video_path):
        os.remove(video_path)
    
    # Delete thumbnail if exists
    if video.get('thumbnail') and video['thumbnail'] != '/static/img/default-thumbnail.jpg':
        thumbnail_path = os.path.join(THUMBNAIL_FOLDER, os.path.basename(video['thumbnail']))
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)
    
    # Delete video from database
    videos_collection.delete_one({'_id': ObjectId(video_id)})
    
    # Delete related comments
    comments_collection.delete_many({'video_id': ObjectId(video_id)})
    
    # Delete related likes
    likes_collection.delete_many({'video_id': ObjectId(video_id)})
    
    # Delete related views
    views_collection.delete_many({'video_id': ObjectId(video_id)})
    
    return jsonify({'success': True, 'message': 'Video deleted successfully'})

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    if not user_data:
        flash('User not found!', 'error')
        return redirect(url_for('index'))
    
    # Get user's videos
    user_videos = list(videos_collection.find({'user_id': ObjectId(current_user.id)}).sort('created_at', -1))
    
    # Calculate statistics - handle subscribers field properly
    subscribers = user_data.get('subscribers', [])
    if isinstance(subscribers, int):
        subscriber_count = subscribers
    else:
        subscriber_count = len(subscribers) if subscribers else 0
    
    total_views = sum(video.get('views', 0) for video in user_videos)
    
    # Add user info to videos for display
    for video in user_videos:
        video['user_info'] = user_data
    
    return render_template('profile.html', 
                         user=user_data,
                         user_videos=user_videos,
                         subscriber_count=subscriber_count,
                         total_views=total_views,
                         is_subscribed=False)  # User can't subscribe to themselves

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'message': 'Both passwords are required'})
    
    # Get current user data
    user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    if not user_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Verify current password
    if not bcrypt.checkpw(current_password.encode('utf-8'), user_data['password']):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    
    # Update password
    users_collection.update_one(
        {'_id': ObjectId(current_user.id)},
        {'$set': {'password': hashed_password}}
    )
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account and all associated data"""
    # Get user data
    user_data = users_collection.find_one({'_id': ObjectId(current_user.id)})
    if not user_data:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Delete all user's videos
    user_videos = list(videos_collection.find({'user_id': ObjectId(current_user.id)}))
    for video in user_videos:
        # Delete video file
        video_path = os.path.join(VIDEO_FOLDER, video['filename'])
        if os.path.exists(video_path):
            os.remove(video_path)
        
        # Delete thumbnail
        if video.get('thumbnail') and video['thumbnail'] != '/static/img/default-thumbnail.jpg':
            thumbnail_path = os.path.join(THUMBNAIL_FOLDER, os.path.basename(video['thumbnail']))
            if os.path.exists(thumbnail_path):
                os.remove(thumbnail_path)
    
    # Delete from database
    videos_collection.delete_many({'user_id': ObjectId(current_user.id)})
    comments_collection.delete_many({'user_id': ObjectId(current_user.id)})
    likes_collection.delete_many({'user_id': ObjectId(current_user.id)})
    views_collection.delete_many({'user_id': ObjectId(current_user.id)})
    
    # Remove user from others' subscribers list
    users_collection.update_many(
        {'subscribers': current_user.id},
        {'$pull': {'subscribers': current_user.id}}
    )
    
    # Delete user account
    users_collection.delete_one({'_id': ObjectId(current_user.id)})
    
    # Logout user
    logout_user()
    
    return jsonify({'success': True, 'message': 'Account deleted successfully'})

if __name__ == '__main__':
    # Create sample data on startup
    create_sample_data()
    
    print("🎉 YouTube Clone is starting up...")
    print("📱 Access the application at: http://localhost:5000")
    print("👤 Demo login available at: http://localhost:5000/demo-login")
    print("🔑 Demo credentials: username: demo_user1, password: password123")
    print("🚀 All features are ready to use!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)



