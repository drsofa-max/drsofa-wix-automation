from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ ENABLE CORS FOR GITHUB PAGES
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

@app.route('/api/posts/generate', methods=['POST', 'OPTIONS'])
def generate_post():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json()
    
    # Demo response
    return jsonify({
        'post': {
            'title': f"Blog Post Generated",
            'meta_description': 'Generated post from AI',
            'body': 'This is a generated blog post',
            'status': 'draft'
        }
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
