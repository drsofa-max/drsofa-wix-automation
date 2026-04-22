import requests
import json
from datetime import datetime

class WixPublisher:
    def __init__(self, api_key, account_id, proxy_url, site_id):
        """Initialize Wix API publisher"""
        self.api_key = api_key
        self.account_id = account_id
        self.proxy_url = proxy_url.rstrip('/')
        self.site_id = site_id
        self.headers = {
            'Authorization': self.api_key,
            'wix-site-id': self.site_id,
            'wix-account-id': self.account_id,
            'Content-Type': 'application/json'
        }
    
    def publish_post(self, title, meta_description, body, status='DRAFT'):
        """
        Publish post to Wix blog
        
        Args:
            title: Post title
            meta_description: SEO meta description
            body: Post body (markdown or plain text)
            status: 'DRAFT' or 'PUBLISHED'
        
        Returns:
            {
                'success': bool,
                'post_id': str (if success),
                'post_url': str (if success),
                'error': str (if error)
            }
        """
        
        try:
            url = f"{self.proxy_url}/wix/blog/v3/posts"
            
            # Convert body paragraphs to Wix rich content format
            paragraphs = [p.strip() for p in body.split('\n\n') if p.strip()]
            
            nodes = []
            for para in paragraphs:
                if para.startswith('##'):
                    # Heading
                    heading_text = para.replace('##', '').strip()
                    nodes.append({
                        "type": "HEADING",
                        "nodes": [{"type": "TEXT", "textData": {"text": heading_text}}]
                    })
                elif para.startswith('#'):
                    # Skip H1 (usually title)
                    continue
                else:
                    # Regular paragraph
                    nodes.append({
                        "type": "PARAGRAPH",
                        "nodes": [{"type": "TEXT", "textData": {"text": para}}]
                    })
            
            payload = {
                "post": {
                    "title": title,
                    "richContent": {"nodes": nodes},
                    "status": status,
                    "seoData": {
                        "metaDescription": meta_description
                    }
                }
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                post_id = data.get('post', {}).get('id')
                post_url = data.get('post', {}).get('url')
                
                return {
                    'success': True,
                    'post_id': post_id,
                    'post_url': post_url,
                    'status': status
                }
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('message', f'HTTP {response.status_code}')
                
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout - Wix API not responding'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error - check Cloudflare proxy URL'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error publishing to Wix: {str(e)}'
            }
    
    def test_connection(self):
        """Test Wix API connection"""
        try:
            url = f"{self.proxy_url}/wix/blog/v3/posts?limit=1"
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10
            )
            
            return {
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'message': 'Connection successful' if response.status_code == 200 else response.text[:200]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
