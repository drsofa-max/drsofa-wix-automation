from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import Credentials, Site
import requests
import json

credentials_bp = Blueprint('credentials', __name__)

@credentials_bp.route('/save', methods=['POST'])
@jwt_required()
def save_credentials():
    """Save Wix API credentials"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    required_fields = ['wix_api_key', 'wix_account_id', 'cloudflare_proxy_url']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if credentials exist
    creds = Credentials.query.filter_by(user_id=user_id).first()
    
    if creds:
        creds.wix_account_id = data['wix_account_id']
        creds.cloudflare_proxy_url = data['cloudflare_proxy_url'].rstrip('/')
        creds.encrypt_api_key(data['wix_api_key'])
    else:
        creds = Credentials(user_id=user_id)
        creds.wix_account_id = data['wix_account_id']
        creds.cloudflare_proxy_url = data['cloudflare_proxy_url'].rstrip('/')
        creds.encrypt_api_key(data['wix_api_key'])
        db.session.add(creds)
    
    # Also save sites if provided
    if 'sites' in data:
        for site_data in data['sites']:
            site = Site.query.filter_by(
                user_id=user_id,
                wix_site_id=site_data['wix_site_id']
            ).first()
            
            if not site:
                site = Site(
                    user_id=user_id,
                    site_name=site_data['site_name'],
                    domain=site_data['domain'],
                    wix_site_id=site_data['wix_site_id'],
                    city=site_data['city'],
                    state=site_data['state']
                )
                db.session.add(site)
    
    db.session.commit()
    
    return jsonify({'message': 'Credentials saved successfully'}), 200

@credentials_bp.route('/test', methods=['POST'])
@jwt_required()
def test_connection():
    """Test Wix API connection"""
    user_id = get_jwt_identity()
    creds = Credentials.query.filter_by(user_id=user_id).first()
    
    if not creds:
        return jsonify({'error': 'Credentials not found. Save credentials first.'}), 404
    
    try:
        api_key = creds.decrypt_api_key()
        proxy_url = creds.cloudflare_proxy_url
        
        # Get first site to test
        site = Site.query.filter_by(user_id=user_id).first()
        if not site:
            return jsonify({'error': 'No sites configured'}), 400
        
        # Test connection via proxy
        headers = {
            'Authorization': api_key,
            'wix-site-id': site.wix_site_id,
            'wix-account-id': creds.wix_account_id
        }
        
        url = f"{proxy_url}/wix/blog/v3/posts?limit=1"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'message': '✅ Connection successful! API and Wix are working.',
                'status': 'connected',
                'site_tested': site.site_name
            }), 200
        elif response.status_code == 401:
            return jsonify({
                'error': '❌ 401 Unauthorized - Check API key or blog page',
                'status': 'unauthorized'
            }), 401
        else:
            return jsonify({
                'error': f'Wix API error: {response.status_code}',
                'status': 'error',
                'details': response.text[:200]
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({
            'error': 'Connection timeout - check Cloudflare proxy URL',
            'status': 'timeout'
        }), 504
    except Exception as e:
        return jsonify({
            'error': f'Error: {str(e)}',
            'status': 'error'
        }), 500

@credentials_bp.route('/get', methods=['GET'])
@jwt_required()
def get_credentials():
    """Get saved credentials (without API key)"""
    user_id = get_jwt_identity()
    creds = Credentials.query.filter_by(user_id=user_id).first()
    
    if not creds:
        return jsonify({'error': 'Credentials not found'}), 404
    
    return jsonify({
        'wix_account_id': creds.wix_account_id,
        'cloudflare_proxy_url': creds.cloudflare_proxy_url,
        'created_at': creds.created_at.isoformat(),
        'updated_at': creds.updated_at.isoformat()
    }), 200

@credentials_bp.route('/sites', methods=['GET'])
@jwt_required()
def get_sites():
    """Get all configured sites"""
    user_id = get_jwt_identity()
    sites = Site.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'sites': [
            {
                'id': site.id,
                'site_name': site.site_name,
                'domain': site.domain,
                'wix_site_id': site.wix_site_id,
                'city': site.city,
                'state': site.state,
                'blog_active': site.blog_active
            }
            for site in sites
        ]
    }), 200
