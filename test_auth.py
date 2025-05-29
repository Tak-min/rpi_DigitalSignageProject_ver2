#!/usr/bin/env python3
"""
認証システムのテストスクリプト
"""
import requests
import json

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
