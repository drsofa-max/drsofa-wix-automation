from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Post, Schedule, Site
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)

@stats_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    user_id = get_jwt_identity()
    
    # Count posts by status
    total_posts = Post.query.filter_by(user_id=user_id).count()
    published_posts = Post.query.filter_by(user_id=user_id, status='published').count()
    draft_posts = Post.query.filter_by(user_id=user_id, status='draft').count()
    failed_posts = Post.query.filter_by(user_id=user_id, status='failed').count()
    
    # Sites
    total_sites = Site.query.filter_by(user_id=user_id).count()
    active_sites = Site.query.filter_by(user_id=user_id, blog_active=True).count()
    
    # Schedules
    enabled_schedules = Schedule.query.filter_by(user_id=user_id, enabled=True).count()
    
    # Posts this month
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    posts_this_month = Post.query.filter_by(user_id=user_id).filter(
        Post.created_at >= thirty_days_ago
    ).count()
    
    # Latest 5 posts
    latest_posts = Post.query.filter_by(user_id=user_id).order_by(
        Post.created_at.desc()
    ).limit(5).all()
    
    return jsonify({
        'overview': {
            'total_posts': total_posts,
            'published_posts': published_posts,
            'draft_posts': draft_posts,
            'failed_posts': failed_posts,
            'posts_this_month': posts_this_month
        },
        'sites': {
            'total_sites': total_sites,
            'active_sites': active_sites
        },
        'automation': {
            'enabled_schedules': enabled_schedules
        },
        'recent_posts': [
            {
                'id': post.id,
                'title': post.title,
                'site_name': post.site.site_name,
                'status': post.status,
                'created_at': post.created_at.isoformat()
            }
            for post in latest_posts
        ]
    }), 200

@stats_bp.route('/posts-by-month', methods=['GET'])
@jwt_required()
def get_posts_by_month():
    """Get posts grouped by month for chart"""
    user_id = get_jwt_identity()
    
    # Get last 12 months
    posts = Post.query.filter_by(user_id=user_id).all()
    
    # Group by month
    months = {}
    for post in posts:
        month_key = post.created_at.strftime('%Y-%m')
        months[month_key] = months.get(month_key, 0) + 1
    
    # Sort and format
    sorted_months = sorted(months.items())
    
    return jsonify({
        'months': [
            {
                'month': month,
                'count': count
            }
            for month, count in sorted_months
        ]
    }), 200

@stats_bp.route('/posts-by-status', methods=['GET'])
@jwt_required()
def get_posts_by_status():
    """Get posts distribution by status"""
    user_id = get_jwt_identity()
    
    draft = Post.query.filter_by(user_id=user_id, status='draft').count()
    published = Post.query.filter_by(user_id=user_id, status='published').count()
    failed = Post.query.filter_by(user_id=user_id, status='failed').count()
    
    return jsonify({
        'draft': draft,
        'published': published,
        'failed': failed
    }), 200

@stats_bp.route('/posts-by-site', methods=['GET'])
@jwt_required()
def get_posts_by_site():
    """Get posts distribution by site"""
    user_id = get_jwt_identity()
    
    sites = Site.query.filter_by(user_id=user_id).all()
    
    site_stats = []
    for site in sites:
        post_count = Post.query.filter_by(site_id=site.id).count()
        published_count = Post.query.filter_by(site_id=site.id, status='published').count()
        
        site_stats.append({
            'site_id': site.id,
            'site_name': site.site_name,
            'total_posts': post_count,
            'published_posts': published_count
        })
    
    return jsonify({'sites': site_stats}), 200

@stats_bp.route('/topics', methods=['GET'])
@jwt_required()
def get_topic_distribution():
    """Get distribution of posts by topic"""
    user_id = get_jwt_identity()
    
    posts = Post.query.filter_by(user_id=user_id).all()
    
    topics = {}
    for post in posts:
        topic = post.topic or 'unknown'
        topics[topic] = topics.get(topic, 0) + 1
    
    return jsonify({
        'topics': [
            {
                'topic': topic,
                'count': count
            }
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)
        ]
    }), 200
