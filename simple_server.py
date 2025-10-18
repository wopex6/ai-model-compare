from flask import Flask, request, jsonify
from integrated_database import IntegratedDatabase

app = Flask(__name__)
db = IntegratedDatabase()

@app.route('/test-login', methods=['POST'])
def test_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    print(f"Testing: username='{username}', password='{password}'")
    
    user = db.authenticate_user(username, password)
    
    if user:
        return jsonify({'success': True, 'user': user})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True, port=5001)
