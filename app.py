import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'drsofa-wix-automation'}), 200

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'API is running'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
