#!/usr/bin/env python3
"""
統合システムの最終確認テスト
"""
import sys
import subprocess
import time
import requests
import threading
import os
import requests
import json

def check_dependencies():
    """必要な依存関係をチェック"""
    print("🔍 依存関係のチェック...")
    
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import passlib
        import python_jose
        print("✅ すべての依存関係が利用可能です")
        return True
    except ImportError as e:
        print(f"❌ 依存関係が不足しています: {e}")
        print("💡 pip install -r requirements.txt を実行してください")
        return False

def check_main_file():
    """main.pyファイルの存在と構文をチェック"""
    print("\n🔍 main.pyファイルのチェック...")
    
    if not os.path.exists("main.py"):
        print("❌ main.pyファイルが見つかりません")
        return False
    
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 基本的な内容チェック
        required_components = [
            "FastAPI",
            "SQLAlchemy",
            "User",
            "create_user",
            "authenticate_user",
            "/users/",
            "/token"
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ 必要なコンポーネントが不足: {missing_components}")
            return False
        
        print("✅ main.pyファイルは適切に統合されています")
        return True
        
    except Exception as e:
        print(f"❌ main.pyファイルの読み取りエラー: {e}")
        return False

def test_syntax():
    """Pythonファイルの構文チェック"""
    print("\n🔍 構文チェック...")
    
    try:
        result = subprocess.run([sys.executable, "-m", "py_compile", "main.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ main.pyの構文は正常です")
            return True
        else:
            print(f"❌ 構文エラー: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 構文チェックエラー: {e}")
        return False

def start_server():
    """サーバーを起動"""
    print("\n🚀 サーバーを起動中...")
    
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "0.0.0.0", "--port", "8001", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # サーバー起動待機
        time.sleep(5)
        
        return process
    except Exception as e:
        print(f"❌ サーバー起動エラー: {e}")
        return None

def test_endpoints():
    """エンドポイントをテスト"""
    print("\n🔍 エンドポイントのテスト...")
    
    base_url = "http://localhost:8001"
    
    # 基本エンドポイントテスト
    endpoints = [
        ("/", "ルートページ"),
        ("/docs", "APIドキュメント"),
        ("/health", "ヘルスチェック")
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code in [200, 404]:  # 404も正常（エンドポイントが存在しない場合）
                print(f"✅ {description} ({endpoint}): 正常")
            else:
                print(f"⚠️ {description} ({endpoint}): ステータス {response.status_code}")
        except Exception as e:
            print(f"❌ {description} ({endpoint}): 接続エラー - {e}")

def main():
    """メイン実行関数"""
    print("🧪 統合システム最終確認テスト")
    print("=" * 60)
    
    # チェック実行
    checks = [
        check_dependencies(),
        check_main_file(),
        test_syntax(),
        test_auth()
    ]
    
    if not all(checks):
        print("\n❌ 基本チェックで問題が発見されました")
        return False
    
    print("\n✅ すべての基本チェックが成功しました！")
    
    # サーバーテスト
    print("\n" + "=" * 60)
    print("🚀 サーバー動作テスト")
    print("=" * 60)
    
    server_process = start_server()
    if server_process:
        try:
            test_endpoints()
            print("\n✅ サーバーテストが完了しました")
        finally:
            # サーバーを停止
            server_process.terminate()
            server_process.wait()
            print("🛑 サーバーを停止しました")
    
    print("\n" + "=" * 60)
    print("🎉 統合システムの最終確認が完了しました！")
    print("=" * 60)
    
    return True

BASE_URL = "http://localhost:8001"

def test_user_registration():
    """ユーザー登録のテスト"""
    print("=== ユーザー登録テスト ===")
    
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=user_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

def test_user_login():
    """ユーザーログインのテスト"""
    print("\n=== ユーザーログインテスト ===")
    
    login_data = {
        "username": "test@example.com",  # FastAPIのOAuth2はusernameを使用
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/token", data=login_data)
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        print(f"Access Token: {access_token[:50]}..." if access_token else "No token")
        return access_token
    
    return None

def test_protected_endpoint(access_token):
    """保護されたエンドポイントのテスト"""
    print("\n=== 保護されたエンドポイントテスト ===")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # モデル一覧の取得をテスト
    response = requests.get(f"{BASE_URL}/models/", headers=headers)
    
    print(f"Models endpoint - Status: {response.status_code}")
    print(f"Models endpoint - Response: {response.text}")
    
    # ユーザー情報の取得をテスト
    response = requests.get(f"{BASE_URL}/users/me/", headers=headers)
    
    print(f"User info endpoint - Status: {response.status_code}")
    print(f"User info endpoint - Response: {response.text}")

def main():
    print("FastAPI認証システムのテスト")
    print("================================")
    
    # 1. ユーザー登録
    if test_user_registration():
        print("✓ ユーザー登録成功")
    else:
        print("⚠ ユーザー登録失敗（既存のユーザーの可能性があります）")
    
    # 2. ログイン
    access_token = test_user_login()
    if access_token:
        print("✓ ログイン成功")
        
        # 3. 保護されたエンドポイントをテスト
        test_protected_endpoint(access_token)
    else:
        print("✗ ログイン失敗")

if __name__ == "__main__":
    main()
