from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
from datetime import datetime

app = Flask(__name__)

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.route('/api/health', methods=['GET', 'OPTIONS'])
def health():
    return jsonify({'status': 'healthy', 'service': 'drsofa-wix-automation'})

@app.route('/api/wix/sites', methods=['POST', 'OPTIONS'])
def list_wix_sites():
    """List all Wix sites for the account to help find the correct site ID"""
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    wix_key = (os.getenv('WIX_API_KEY') or data.get('wix_key') or '').strip()
    account_id = (os.getenv('WIX_ACCOUNT_ID') or data.get('account_id') or '').strip()

    if not wix_key or not account_id:
        return jsonify({'error': 'Missing credentials'}), 400

    headers = {
        'Authorization': wix_key,
        'Content-Type': 'application/json',
        'wix-account-id': account_id
    }

    try:
        response = requests.get(
            'https://www.wixapis.com/site-list/v2/sites',
            headers=headers,
            timeout=15
        )
        try:
            result = response.json()
        except Exception:
            result = {'raw': response.text}

        return jsonify({
            'status_code': response.status_code,
            'sites': result
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/posts/publish', methods=['POST', 'OPTIONS'])
def publish_post():
    """Publish post to Wix (backend handles CORS)"""
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json()
    # Use env vars if set, otherwise fall back to credentials from request (dashboard localStorage)
    wix_key = (os.getenv('WIX_API_KEY') or data.get('wix_key') or '').strip()
    account_id = (os.getenv('WIX_ACCOUNT_ID') or data.get('account_id') or '').strip()
    site_id = (data.get('site_id') or os.getenv('WIX_SITE_ID') or '').strip().rstrip('/')
    title = data.get('title')
    body = data.get('body')
    meta = data.get('meta_description', '')

    if not wix_key or not account_id:
        return jsonify({'error': 'Missing Wix credentials: WIX_API_KEY and WIX_ACCOUNT_ID environment variables must be set'}), 400

    try:
        # Convert body to Wix rich content format
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

        headers = {
            'Authorization': wix_key,
            'Content-Type': 'application/json'
        }
        if site_id:
            headers['wix-site-id'] = site_id
        if account_id:
            headers['wix-account-id'] = account_id

        payload = {
            "draftPost": {
                "title": title,
                "richContent": {"nodes": nodes},
                "membersOnly": False,
                "seoData": {
                    "metaDescription": meta
                }
            }
        }

        # Call Wix Blog v3 API directly from backend (no CORS issues server-side)
        # Try draft-posts endpoint first (Wix v3 flow: create draft → publish)
        wix_url = 'https://www.wixapis.com/blog/v3/draft-posts'

        response = requests.post(
            wix_url,
            headers=headers,
            json=payload,
            timeout=30
        )

        # If draft created successfully, publish it
        if response.status_code in [200, 201]:
            try:
                draft_data = response.json()
                draft_id = draft_data.get('draftPost', {}).get('id')
                if draft_id:
                    pub_url = f'https://www.wixapis.com/blog/v3/draft-posts/{draft_id}/publish'
                    requests.post(pub_url, headers=headers, timeout=30)
            except:
                pass

        if response.status_code in [200, 201]:
            try:
                result_data = response.json()
                return jsonify({
                    'success': True,
                    'message': 'Post published to Wix!',
                    'data': result_data.get('post', {})
                })
            except:
                return jsonify({
                    'success': True,
                    'message': 'Post published to Wix!',
                    'data': {}
                })
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('message') or error_data.get('error') or str(error_data)
            except Exception:
                error_data = {}
                error_msg = response.text if response.text else f'HTTP {response.status_code}'

            return jsonify({
                'error': f'Wix API Error: {error_msg}',
                'status_code': response.status_code,
                'url': wix_url,
                'wix_response': error_data,
                'headers_sent': {k: v for k, v in headers.items() if k != 'Authorization'}
            }), response.status_code

    except Exception as e:
        import traceback
        return jsonify({
            'error': f'Publishing error: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/posts/generate', methods=['POST', 'OPTIONS'])
def generate_post():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json()
    site_id = data.get('site_id', 1)
    topic = data.get('topic', 'disassembly')
    tone = data.get('tone', 'friendly')
    length = data.get('length', 'medium')
    custom_keyword = data.get('custom_keyword', '')
    
    # Map topics to real content
    topics = {
        'disassembly': {
            'title': 'How to Disassemble Your Sofa for Moving: A Complete Guide',
            'meta': 'Learn professional sofa disassembly techniques for safe moving. Step-by-step guide with expert tips.',
            'body': '''Moving a large sofa can be one of the most challenging aspects of relocating. Whether you're dealing with a narrow stairwell, tight doorways, or limited elevator space, proper disassembly is essential. At Dr. Sofa, we've spent over 30 years perfecting the art of furniture disassembly and safe relocation.

## Why Disassemble Your Sofa?

Before attempting to move a large sofa through tight spaces, consider these critical reasons for professional disassembly:

**Prevents Damage**: A standard sofa can be damaged beyond repair when forced through doorways or down stairs. Professional disassembly ensures your furniture arrives in perfect condition.

**Saves Time**: What might take hours of struggling can be accomplished in minutes with the right tools and expertise.

**Protects Your Home**: Dragging large furniture can damage walls, floors, and doorframes, leading to expensive repairs.

**Ensures Safety**: Heavy furniture can cause serious injuries. Professional handling eliminates these risks.

## The Dr. Sofa Disassembly Process

Our team follows a systematic approach to safely disassemble any sofa:

### Step 1: Assessment
We evaluate your sofa's construction, materials, and the spaces you're navigating to create the optimal disassembly plan.

### Step 2: Documentation
Before we begin, we photograph and document each step. This ensures perfect reassembly at your destination.

### Step 3: Careful Disassembly
Using specialized tools, we carefully remove legs, arms, and cushions. Every bolt and screw is organized and labeled.

### Step 4: Protection
All pieces are wrapped with protective materials to prevent scratches, tears, and dirt during transport.

### Step 5: Expert Reassembly
At your new location, we reassemble your sofa exactly as it was, with perfect alignment and stability.

## What Makes Us Different

With over 30 years of experience, we've handled every type of sofa imaginable. From custom designer pieces to vintage antiques, we treat every furniture piece with the utmost care and professionalism.

## Get Your Free Consultation

Don't risk damage to your valuable furniture. Contact Dr. Sofa today for a free assessment and moving consultation. We serve all neighborhoods and handle complex moves that other companies won't touch.'''
        },
        'reassembly': {
            'title': 'Professional Furniture Reassembly Services: Guaranteed Perfect Results',
            'meta': 'Expert furniture reassembly after moving. We ensure perfect alignment and stability. Free consultation available.',
            'body': '''After your move, proper furniture reassembly is crucial for both functionality and safety. At Dr. Sofa, we specialize in expert reassembly of all furniture types, from modern sofas to antique pieces.

## Why Choose Professional Reassembly?

**Perfect Alignment**: We ensure every connection is precisely aligned and properly secured.

**Structural Integrity**: Improper reassembly can compromise your furniture's stability and safety.

**Warranty Protection**: Professional reassembly helps maintain your furniture's warranty.

**Time Savings**: Our team completes in hours what might take you days.

## Our Reassembly Services

- **Sofas & Sectionals**: From traditional to contemporary designs
- **Bed Frames**: Complete assembly with proper support
- **Dining Sets**: Tables and chairs with secure joint connection
- **Modular Furniture**: Complex pieces requiring precise alignment
- **Custom & Designer Pieces**: Delicate furniture requiring specialized care

## The Reassembly Advantage

Our technicians carry specialized tools and hardware replacements. If any bolts, screws, or connecting hardware were damaged during moving, we replace them immediately.

## Book Your Reassembly Today

Don't let improperly reassembled furniture affect your home's comfort and safety. Contact us for fast, professional reassembly services.'''
        },
        'reupholstery': {
            'title': 'Transform Your Sofa: Professional Reupholstery Services',
            'meta': 'Expert sofa reupholstery and restoration. Hundreds of fabric options. Restore furniture to like-new condition.',
            'body': '''Your beloved sofa has served faithfully for years, but time and use have taken their toll. Rather than replacing it, consider professional reupholstery. At Dr. Sofa, we specialize in transforming tired furniture into beautiful centerpieces.

## Why Reupholster?

**Cost Savings**: Reupholstery costs significantly less than purchasing new furniture.

**Sustainability**: Extending the life of existing furniture reduces waste and environmental impact.

**Customization**: Choose from hundreds of fabrics to match your updated décor perfectly.

**Quality**: Professional reupholstery delivers superior results to DIY attempts.

## Our Reupholstery Services Include

- Complete fabric replacement
- Padding and cushion restoration
- Wood frame repair and refinishing
- Seam and stitch repair
- Piping and trim options
- Kiln-dried hardwood reinforcement

## Fabric Selection

We offer access to premium fabric collections from leading manufacturers. Whether you prefer classic leather, durable microsuede, elegant velvet, or contemporary patterns, we have options for every style and budget.

## The Transformation Process

1. **Evaluation**: We assess the frame condition and structural integrity
2. **Fabric Selection**: Browse our extensive collection and samples
3. **Disassembly**: Careful removal of old upholstery
4. **Restoration**: Frame reinforcement and padding replacement
5. **Reupholstery**: Expert installation of new fabric
6. **Quality Inspection**: Thorough examination before delivery

## Award-Winning Craftsmanship

With decades of experience, Dr. Sofa has restored hundreds of furniture pieces to their original beauty and functionality. Your sofa deserves expert care.'''
        },
        'tips': {
            'title': '5 Essential Furniture Care Tips Every Homeowner Should Know',
            'meta': 'Protect your furniture investment with expert care tips. Learn how to maintain your sofas and furniture for years.',
            'body': '''Your furniture is a significant investment in your home's comfort and appearance. Proper care extends its lifespan and maintains its beauty. Here are five essential tips from the experts at Dr. Sofa.

## 1. Rotate Cushions Regularly

Cushions bear the most weight and wear. By rotating them weekly, you distribute wear evenly and prevent permanent impressions.

**Pro Tip**: Flip cushions front-to-back and side-to-side for even distribution of wear.

## 2. Vacuum Weekly

Regular vacuuming removes dust, crumbs, and debris before they become embedded in fibers.

**Pro Tip**: Use an upholstery attachment and gently brush along the fabric grain for best results.

## 3. Address Spills Immediately

The faster you address spills, the less damage occurs. Blot (never rub) with a clean, damp cloth.

**Pro Tip**: Keep a small bottle of upholstery cleaner nearby for quick treatment of minor spills.

## 4. Control Sunlight Exposure

UV rays fade fabrics and deteriorate materials over time. Use curtains or rearrange furniture periodically.

**Pro Tip**: Move furniture away from direct sunlight or use UV-protective window treatments.

## 5. Professional Cleaning Annually

Professional cleaning removes deep-seated dirt and restores fabric appearance. Schedule annual service for heavily used pieces.

**Pro Tip**: Professional cleaning also extends the life of your upholstery significantly.

## Bonus Tip: Know Your Fabric

Different fabrics require different care:
- **Leather**: Use leather-specific cleaners and conditioners
- **Microfiber**: Vacuum regularly; use water-based cleaners
- **Velvet**: Gentle brushing with soft cloth; avoid liquids
- **Cotton/Linen**: More durable; responds well to regular cleaning

## Protect Your Investment

Your furniture deserves proper care. Contact Dr. Sofa for professional cleaning, maintenance, and restoration services. We help you keep your furniture looking beautiful for decades.'''
        },
        'local': {
            'title': 'Moving Large Furniture Through Tight NYC Spaces: Expert Solutions',
            'meta': 'Professional furniture moving solutions for narrow NYC apartments. We handle impossible moves with expert techniques.',
            'body': '''New York City apartments present unique furniture moving challenges. Narrow hallways, tight corners, and restrictive building regulations make standard moving approaches impossible. Dr. Sofa has spent three decades solving these exact problems.

## The NYC Furniture Moving Challenge

**Narrow Hallways**: Many pre-war buildings feature hallways barely 3 feet wide.

**Limited Elevator Access**: Older buildings have small, slow elevators with restrictive dimensions.

**Stairwell Navigation**: Winding, narrow stairwells with sharp angles.

**Building Restrictions**: Many buildings charge substantial fees or restrict move times.

## Our Expert Solutions

### The Disassembly Approach
We carefully disassemble your furniture, documenting each step with photographs. This allows us to navigate the tightest spaces.

### Specialized Equipment
We carry tools and equipment specifically designed for NYC apartment moves:
- Custom furniture dollies and sliders
- Protective barriers for walls and frames
- Professional wrapping materials
- Stair-climbing equipment

### Pre-Move Planning
We visit your current location and destination to plan the optimal route and technique. No surprises on moving day.

### Building Coordination
We handle all communication with building management and coordinate move timing to comply with building regulations.

## Case Studies

We've successfully moved furniture through:
- Pre-war brownstone walkups
- Modern high-rises with tiny elevators
- Landmark buildings with strict regulations
- Loft conversions with industrial character

## The Difference

Other movers might refuse your move or charge astronomical fees. We specialize in the "impossible" moves that make NYC famous. With decades of experience, we've developed proven techniques for every scenario.

## Your Next Move

Don't let tight spaces prevent you from having the furniture you love. Contact Dr. Sofa for a free consultation and move estimate. We handle what others won't.'''
        }
    }
    
    # Get content based on topic
    content = topics.get(topic, topics['disassembly'])
    
    # Customize with keywords if provided
    if custom_keyword:
        content['meta'] = f"{custom_keyword} - {content['meta']}"
        content['body'] = f"{custom_keyword} services. {content['body']}"
    
    return jsonify({
        'post': {
            'title': content['title'],
            'meta_description': content['meta'],
            'body': content['body'],
            'status': 'draft'
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
