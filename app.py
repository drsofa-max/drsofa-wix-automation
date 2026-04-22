from flask import Flask, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'drsofa-wix-automation',
        'message': 'Backend is running!'
    }), 200

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Dr. Sofa Wix Automation API'}), 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
