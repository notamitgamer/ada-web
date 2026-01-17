#!/usr/bin/env python3
"""
Simple test script to verify backend.py imports and basic functionality
"""

import sys
import os

# Set a dummy API key for import testing
os.environ['GEMINI_API_KEY'] = 'test_key_for_import'

print("Testing backend.py imports and structure...")

try:
    # Test imports
    from flask import Flask, request, jsonify, Response, stream_with_context
    from flask_cors import CORS
    import google.generativeai as genai
    print("✅ All required packages imported successfully")
    
    # Test that backend.py can be imported
    import backend
    print("✅ backend.py imported successfully")
    
    # Check if Flask app exists
    assert hasattr(backend, 'app'), "Flask app not found"
    print("✅ Flask app exists")
    
    # Check if routes are defined
    routes = [rule.rule for rule in backend.app.url_map.iter_rules()]
    expected_routes = ['/', '/api/chat', '/api/generate-title']
    
    for route in expected_routes:
        assert route in routes, f"Route {route} not found"
        print(f"✅ Route {route} is defined")
    
    # Check if verify_token function exists
    assert hasattr(backend, 'verify_token'), "verify_token function not found"
    print("✅ verify_token function exists")
    
    # Check model name
    model_name = backend.model.model_name
    print(f"✅ Model configured: {model_name}")
    
    if "gemini-2.5-flash-preview" in model_name or model_name == "models/gemini-2.5-flash-preview-09-2025":
        print("✅ Correct model version configured!")
    else:
        print(f"⚠️  Warning: Model is {model_name}, expected gemini-2.5-flash-preview-09-2025")
    
    print("\n" + "="*50)
    print("✅ ALL TESTS PASSED!")
    print("="*50)
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except AssertionError as e:
    print(f"❌ Assertion Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {type(e).__name__}: {e}")
    sys.exit(1)
