"""
Admin Dashboard for YouTube Clone
Monitor users, videos, and analytics
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from pymongo import MongoClient
from datetime import datetime, timedelta
import json

# Import from main app
from app import db, users_collection, videos_collection, comments_collection, likes_collection, views_collection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def is_admin():
    """Check if current user is admin"""
    if not current_user.is_authenticated:
        return False
    
    user = users_collection.find_one({'_id': current_user.id})
    return user and user.get('role') == 'admin'

@admin_bp.before_request
def require_admin():
    """Require admin access for all admin routes"""
    if not is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))

@admin_bp.route('/')
@login_required
def dashboard():
    """Main admin dashboard"""
    # Get statistics
    total_users = users_collection.count_documents({})
    total_videos = videos_collection.count_documents({})
    total_comments = comments_collection.count_documents({})
    total_likes = likes_collection.count_documents({})
    
    # Recent activity
    recent_users = list(users_collection.find().sort('created_at', -1).limit(5))
    recent_videos = list(videos_collection.find().sort('created_at', -1).limit(5))
    
    # Popular videos
    popular_videos = list(videos_collection.find().sort('view_count', -1).limit(10))
    
    # User growth (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    new_users_30_days = users_collection.count_documents({
        'created_at': {'$gte': thirty_days_ago}
    })
    
    # Video uploads (last 30 days)
    new_videos_30_days = videos_collection.count_documents({
        'created_at': {'$gte': thirty_days_ago}
    })
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_videos=total_videos,
                         total_comments=total_comments,
                         total_likes=total_likes,
                         recent_users=recent_users,
                         recent_videos=recent_videos,
                         popular_videos=popular_videos,
                         new_users_30_days=new_users_30_days,
                         new_videos_30_days=new_videos_30_days)

@admin_bp.route('/users')
@login_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    users_list = list(users_collection.find().sort('created_at', -1).skip(skip).limit(per_page))
    total_users = users_collection.count_documents({})
    total_pages = (total_users + per_page - 1) // per_page
    
    return render_template('admin/users.html',
                         users=users_list,
                         current_page=page,
                         total_pages=total_pages,
                         total_users=total_users)

@admin_bp.route('/videos')
@login_required
def videos():
    """Manage videos"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    videos_list = list(videos_collection.find().sort('created_at', -1).skip(skip).limit(per_page))
    total_videos = videos_collection.count_documents({})
    total_pages = (total_videos + per_page - 1) // per_page
    
    # Get user info for each video
    for video in videos_list:
        user = users_collection.find_one({'_id': video.get('user_id')})
        video['user_info'] = user
    
    return render_template('admin/videos.html',
                         videos=videos_list,
                         current_page=page,
                         total_pages=total_pages,
                         total_videos=total_videos)

@admin_bp.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard"""
    # Get data for charts
    # User registration over time
    user_data = []
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        count = users_collection.count_documents({
            'created_at': {'$gte': start_of_day, '$lt': end_of_day}
        })
        user_data.append({
            'date': start_of_day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Video uploads over time
    video_data = []
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        count = videos_collection.count_documents({
            'created_at': {'$gte': start_of_day, '$lt': end_of_day}
        })
        video_data.append({
            'date': start_of_day.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Top users by video count
    pipeline = [
        {'$group': {'_id': '$user_id', 'video_count': {'$sum': 1}}},
        {'$sort': {'video_count': -1}},
        {'$limit': 10}
    ]
    top_users = list(videos_collection.aggregate(pipeline))
    
    # Get user details for top users
    for user_stat in top_users:
        user = users_collection.find_one({'_id': user_stat['_id']})
        user_stat['user_info'] = user
    
    return render_template('admin/analytics.html',
                         user_data=json.dumps(user_data),
                         video_data=json.dumps(video_data),
                         top_users=top_users)

@admin_bp.route('/user/<user_id>')
@login_required
def user_detail(user_id):
    """User detail page"""
    from bson import ObjectId
    
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('admin.users'))
    
    # Get user's videos
    user_videos = list(videos_collection.find({'user_id': ObjectId(user_id)}).sort('created_at', -1))
    
    # Get user's comments
    user_comments = list(comments_collection.find({'user_id': ObjectId(user_id)}).sort('created_at', -1))
    
    # Get user's likes
    user_likes = list(likes_collection.find({'user_id': ObjectId(user_id)}).sort('created_at', -1))
    
    return render_template('admin/user_detail.html',
                         user=user,
                         videos=user_videos,
                         comments=user_comments,
                         likes=user_likes)

@admin_bp.route('/video/<video_id>')
@login_required
def video_detail(video_id):
    """Video detail page"""
    from bson import ObjectId
    
    video = videos_collection.find_one({'_id': ObjectId(video_id)})
    if not video:
        flash('Video not found.', 'error')
        return redirect(url_for('admin.videos'))
    
    # Get video owner
    user = users_collection.find_one({'_id': video.get('user_id')})
    video['user_info'] = user
    
    # Get video comments
    comments = list(comments_collection.find({'video_id': ObjectId(video_id)}).sort('created_at', -1))
    
    # Get comment authors
    for comment in comments:
        comment_user = users_collection.find_one({'_id': comment.get('user_id')})
        comment['user_info'] = comment_user
    
    return render_template('admin/video_detail.html',
                         video=video,
                         comments=comments)

@admin_bp.route('/delete_user/<user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete user and all their content"""
    from bson import ObjectId
    
    # Delete user's videos
    videos_collection.delete_many({'user_id': ObjectId(user_id)})
    
    # Delete user's comments
    comments_collection.delete_many({'user_id': ObjectId(user_id)})
    
    # Delete user's likes
    likes_collection.delete_many({'user_id': ObjectId(user_id)})
    
    # Delete user
    users_collection.delete_one({'_id': ObjectId(user_id)})
    
    flash('User and all their content deleted successfully.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/delete_video/<video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    """Delete video and all related content"""
    from bson import ObjectId
    
    # Delete video comments
    comments_collection.delete_many({'video_id': ObjectId(video_id)})
    
    # Delete video likes
    likes_collection.delete_many({'video_id': ObjectId(video_id)})
    
    # Delete video views
    views_collection.delete_many({'video_id': ObjectId(video_id)})
    
    # Delete video
    videos_collection.delete_one({'_id': ObjectId(video_id)})
    
    flash('Video and all related content deleted successfully.', 'success')
    return redirect(url_for('admin.videos'))

@admin_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for real-time statistics"""
    total_users = users_collection.count_documents({})
    total_videos = videos_collection.count_documents({})
    total_comments = comments_collection.count_documents({})
    total_likes = likes_collection.count_documents({})
    
    # Today's stats
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_users_today = users_collection.count_documents({
        'created_at': {'$gte': today}
    })
    new_videos_today = videos_collection.count_documents({
        'created_at': {'$gte': today}
    })
    
    return jsonify({
        'total_users': total_users,
        'total_videos': total_videos,
        'total_comments': total_comments,
        'total_likes': total_likes,
        'new_users_today': new_users_today,
        'new_videos_today': new_videos_today
    }) 