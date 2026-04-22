from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'drsofa-wix-automation'})

@app.route('/')
def home():
    return jsonify({'message': 'API running'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
