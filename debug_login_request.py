#!/usr/bin/env python3
"""
Debug what the frontend is actually sending
"""

from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/debug-login', methods=['POST'])
def debug_login():
    """Debug endpoint to see what data is being sent"""
    print("=" * 50)
    print("DEBUG: Login request received")
    print(f"Content-Type: {request.content_type}")
    print(f"Method: {request.method}")
    
    # Try to get JSON data
    try:
        json_data = request.get_json()
        print(f"JSON data: {json_data}")
    except Exception as e:
        print(f"JSON error: {e}")
        json_data = None
    
    # Try to get form data
    try:
        form_data = request.form.to_dict()
        print(f"Form data: {form_data}")
    except Exception as e:
        print(f"Form error: {e}")
        form_data = None
    
    # Try to get raw data
    try:
        raw_data = request.get_data(as_text=True)
        print(f"Raw data: {raw_data}")
    except Exception as e:
        print(f"Raw data error: {e}")
        raw_data = None
    
    print("=" * 50)
    
    return jsonify({
        'received_json': json_data,
        'received_form': form_data,
        'received_raw': raw_data,
        'content_type': request.content_type
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
