#!/usr/bin/env python3
"""
Simple Game Upload Test Script
GameHost Platform - JWT + Game Upload Test

Bu script JWT authentication ve game upload test eder.
"""

import requests
import json
import os
import zipfile
import tempfile
from datetime import datetime
import random

# API Base URL
BASE_URL = "http://127.0.0.1:8000"

def create_simple_game_zip():
    """Basit bir WebGL game ZIP dosyası oluşturur"""
    
    # Temporary dosya oluştur
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "simple_game.zip")
    
    # Basit HTML content
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Simple Test Game</title>
    <style>
        body { 
            margin: 0; 
            padding: 20px; 
            font-family: Arial, sans-serif;
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
        }
        .game-container {
            background: rgba(255,255,255,0.1);
            padding: 40px;
            border-radius: 10px;
            margin: 50px auto;
            max-width: 600px;
        }
        .btn {
            background: #4CAF50;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
        }
        .btn:hover { background: #45a049; }
        #score { font-size: 24px; margin: 20px 0; }
        #game-area {
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            min-height: 200px;
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🎮 Simple Test Game</h1>
        <p>Bu basit bir test oyunudur. GameHost Platform için oluşturulmuştur.</p>
        
        <div id="game-area">
            <p>Butona tıklayarak puan kazanın!</p>
            <div id="score">Puan: <span id="score-value">0</span></div>
            <button class="btn" onclick="addScore()">🎯 Puan Kazın!</button>
            <button class="btn" onclick="resetScore()">🔄 Sıfırla</button>
        </div>
        
        <p><small>Test Date: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</small></p>
    </div>

    <script>
        let score = 0;
        
        function addScore() {
            score += Math.floor(Math.random() * 10) + 1;
            document.getElementById('score-value').textContent = score;
            
            if (score > 50) {
                alert('🎉 Tebrikler! 50 puanı geçtiniz!');
            }
        }
        
        function resetScore() {
            score = 0;
            document.getElementById('score-value').textContent = score;
        }
        
        // Auto-start message
        console.log('Simple Test Game loaded successfully!');
    </script>
</body>
</html>"""
    
    # Dummy JS content for Build/ folder
    loader_js = """// Simple game loader
console.log('Game loader initialized');
var Module = {
    onRuntimeInitialized: function() {
        console.log('Game runtime ready');
    }
};"""
    
    framework_js = """// Simple framework
console.log('Game framework loaded');"""
    
    # ZIP dosyası oluştur - WebGL structure ile
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("index.html", html_content)
        # Build/ klasörü ekle (WebGL oyunları için gerekli)
        zipf.writestr("Build/game.loader.js", loader_js)
        zipf.writestr("Build/game.framework.js", framework_js)
        zipf.writestr("Build/game.data", "dummy_data_content")
        zipf.writestr("Build/game.wasm", "dummy_wasm_content")
        # TemplateData/ klasörü ekle (WebGL template için gerekli)
        zipf.writestr("TemplateData/style.css", "/* Game styles */")
        zipf.writestr("TemplateData/UnityProgress.js", "// Unity progress script")
        zipf.writestr("TemplateData/favicon.ico", "dummy_favicon_content")
    
    print(f"📦 Simple game ZIP created: {zip_path}")
    return zip_path

def test_jwt_game_upload():
    """JWT authentication ve game upload testini yapar"""
    
    print("🎮 JWT GAME UPLOAD TEST")
    print("=" * 50)
    
    # 1. Register (JWT token almak için)
    random_id = random.randint(1000, 9999)
    register_data = {
        "username": f"gametest_{random_id}",
        "email": f"gametest_{random_id}@example.com",
        "password": "testpass123",
        "password2": "testpass123"
    }
    
    print(f"📋 1. Register user: {register_data['username']}")
    
    try:
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register/",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if register_response.status_code == 201:
            register_result = register_response.json()
            print(f"DEBUG: Register response: {register_result}")  # Debug line
            access_token = register_result['tokens']['access']
            print(f"✅ Register successful!")
            print(f"   User ID: {register_result['user']['id']}")
            print(f"   Access Token: {access_token[:50]}...")
        else:
            print(f"❌ Register failed: {register_response.status_code}")
            print(f"   Error: {register_response.text}")
            return
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Register request failed: {e}")
        return
    
    # 2. Game Upload Test
    print(f"\n📋 2. Game Upload Test")
    
    # Basit game ZIP oluştur
    game_zip_path = create_simple_game_zip()
    
    try:
        # Game upload data
        game_data = {
            'title': f'Simple Test Game {random_id}',
            'description': f'Bu JWT authentication ile yüklenen test oyunudur. Upload time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'genre_ids': [5],  # Aksiyon genre (existing ID)
            'tag_ids': [3, 5]  # Arcade, Bulmaca (existing IDs)
        }
        
        # File upload
        files = {
            'webgl_build_zip': ('simple_game.zip', open(game_zip_path, 'rb'), 'application/zip')
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        print(f"   Title: {game_data['title']}")
        print(f"   Description: {game_data['description'][:50]}...")
        print(f"   ZIP Size: {os.path.getsize(game_zip_path)} bytes")
        
        upload_response = requests.post(
            f"{BASE_URL}/api/games/games/",
            data=game_data,
            files=files,
            headers=headers,
            timeout=30
        )
        
        # File'ı kapat
        files['webgl_build_zip'][1].close()
        
        if upload_response.status_code == 201:
            upload_result = upload_response.json()
            print(f"✅ Game upload successful!")
            print(f"   Game ID: {upload_result['id']}")
            print(f"   Title: {upload_result['title']}")
            print(f"   Creator: {upload_result['creator']['username']}")
            print(f"   Status: Published={upload_result['is_published']}")
            print(f"   ZIP URL: {upload_result['game_file_url']}")
            
            # 3. Game Detail Test
            print(f"\n📋 3. Game Detail Test")
            detail_response = requests.get(
                f"{BASE_URL}/api/games/games/{upload_result['id']}/",
                headers=headers,
                timeout=10
            )
            
            if detail_response.status_code == 200:
                detail_result = detail_response.json()
                print(f"✅ Game detail retrieved successfully!")
                print(f"   Entry Point: {detail_result.get('entry_point_url', 'N/A')}")
            else:
                print(f"❌ Game detail failed: {detail_response.status_code}")
                
        else:
            print(f"❌ Game upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Game upload request failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(game_zip_path):
            os.remove(game_zip_path)
            print(f"🧹 Cleanup: Temporary ZIP file removed")

if __name__ == '__main__':
    test_jwt_game_upload() 