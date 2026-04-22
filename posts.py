from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Post, Site, Credentials
from utils.blog_generator import generate_blog_post
from utils.wix_publisher import WixPublisher
from datetime import datetime

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_post():
    """Generate a new blog post"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Validate input
    required_fields = ['site_id', 'topic', 'tone', 'length']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Get site
    site = Site.query.filter_by(id=data['site_id'], user_id=user_id).first()
    if not site:
        return jsonify({'error': 'Site not found'}), 404
    
    # Generate post via OpenAI
    result = generate_blog_post(
        site_name=site.site_name,
        city=site.city,
        state=site.state,
        topic=data['topic'],
        tone=data['tone'],
        length=data['length'],
        custom_keyword=data.get('custom_keyword')
    )
    
    if not result['success']:
        return jsonify({'error': result['error']}), 500
    
    # Save to database
    post = Post(
        user_id=user_id,
        site_id=site.id,
        title=result['title'],
        meta_description=result['meta_description'],
        body=result['body'],
        status='draft',
        topic=data['topic'],
        tone=data['tone'],
        length=data['length']
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({
        'message': 'Post generated successfully',
        'post': {
            'id': post.id,
            'title': post.title,
            'meta_description': post.meta_description,
            'body': post.body,
            'status': post.status,
            'created_at': post.created_at.isoformat()
        }
    }), 201

@posts_bp.route('/<int:post_id>/publish', methods=['POST'])
@jwt_required()
def publish_post(post_id):
    """Publish a post to Wix"""
    user_id = get_jwt_identity()
    
    # Get post
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Get credentials
    creds = Credentials.query.filter_by(user_id=user_id).first()
    if not creds:
        return jsonify({'error': 'Credentials not configured'}), 400
    
    try:
        # Publish via Wix
        api_key = creds.decrypt_api_key()
        publisher = WixPublisher(
            api_key=api_key,
            account_id=creds.wix_account_id,
            proxy_url=creds.cloudflare_proxy_url,
            site_id=post.site.wix_site_id
        )
        
        result = publisher.publish_post(
            title=post.title,
            meta_description=post.meta_description,
            body=post.body,
            status='DRAFT'
        )
        
        if result['success']:
            # Update post
            post.status = 'published'
            post.wix_post_id = result['post_id']
            post.wix_post_url = result['post_url']
            post.published_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'message': 'Post published to Wix as draft',
                'post': {
                    'id': post.id,
                    'wix_post_id': post.wix_post_id,
                    'wix_post_url': post.wix_post_url,
                    'status': post.status
                }
            }), 200
        else:
            # Log error
            post.status = 'failed'
            post.error_message = result['error']
            db.session.commit()
            
            return jsonify({
                'error': result['error'],
                'post_id': post.id
            }), 400
            
    except Exception as e:
        post.status = 'failed'
        post.error_message = str(e)
        db.session.commit()
        
        return jsonify({'error': f'Error publishing: {str(e)}'}), 500

@posts_bp.route('', methods=['GET'])
@jwt_required()
def get_posts():
    """Get all posts for user"""
    user_id = get_jwt_identity()
    
    # Query parameters for filtering
    site_id = request.args.get('site_id', type=int)
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Post.query.filter_by(user_id=user_id)
    
    if site_id:
        query = query.filter_by(site_id=site_id)
    if status:
        query = query.filter_by(status=status)
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    return jsonify({
        'posts': [
            {
                'id': post.id,
                'title': post.title,
                'site_id': post.site_id,
                'site_name': post.site.site_name,
                'status': post.status,
                'topic': post.topic,
                'created_at': post.created_at.isoformat(),
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'wix_post_url': post.wix_post_url
            }
            for post in posts.items
        ],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': page
    }), 200

@posts_bp.route('/<int:post_id>', methods=['GET'])
@jwt_required()
def get_post(post_id):
    """Get single post"""
    user_id = get_jwt_identity()
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    return jsonify({
        'id': post.id,
        'title': post.title,
        'meta_description': post.meta_description,
        'body': post.body,
        'site_id': post.site_id,
        'site_name': post.site.site_name,
        'status': post.status,
        'topic': post.topic,
        'tone': post.tone,
        'length': post.length,
        'created_at': post.created_at.isoformat(),
        'published_at': post.published_at.isoformat() if post.published_at else None,
        'wix_post_url': post.wix_post_url
    }), 200

@posts_bp.route('/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """Delete a post"""
    user_id = get_jwt_identity()
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Post deleted'}), 200
