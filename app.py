from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Simple health check - no database needed
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'drsofa-wix-automation',
        'message': 'Backend is running!'
    }), 200

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        'api': 'operational',
        'database': 'not yet configured',
        'flask_env': os.getenv('FLASK_ENV', 'production')
    }), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error', 'details': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment or default to 5000
    port = int(os.getenv('PORT', 5000))
    # Listen on all interfaces for Railway
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
