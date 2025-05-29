#!/usr/bin/env python3
"""
認証システムの詳細デバッグスクリプト
"""
import requests
import json
import sqlite3
from datetime import datetime, timedelta
from jose import jwt

# 設定
BASE_URL = "http://localhost:8001"
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # auth.pyと同じ
ALGORITHM = "HS256"

def check_database():
    """データベースの状態を確認"""
    print("=== データベース状態確認 ===")
    try:
        conn = sqlite3.connect('database_new.db')
        cursor = conn.cursor()
        
        # テーブル一覧取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"存在するテーブル: {[table[0] for table in tables]}")
        
        # ユーザー一覧取得
        cursor.execute('SELECT id, email, created_at FROM users')
        users = cursor.fetchall()
        print(f"登録ユーザー数: {len(users)}")
        for user in users:
            print(f"  ID: {user[0]}, Email: {user[1]}, Created: {user[2]}")
        
        conn.close()
        return len(users) > 0
    except Exception as e:
        print(f"データベースエラー: {e}")
        return False

def test_server_connection():
    """サーバー接続テスト"""
    print("\n=== サーバー接続テスト ===")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"サーバーステータス: {response.status_code}")
        return True
    except Exception as e:
        print(f"サーバー接続エラー: {e}")
        return False

def create_test_token():
    """テスト用の有効なJWTトークンを手動作成"""
    print("\n=== テストトークン作成 ===")
    
    # ペイロードの作成
    expire = datetime.utcnow() + timedelta(minutes=60)
    payload = {
        "sub": "test@example.com",  # ユーザーのメールアドレス
        "exp": expire
    }
    
    # トークン生成
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print(f"生成されたトークン: {token[:50]}...")
    
    # トークンデコードテスト
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"デコード成功: {decoded}")
        return token
    except Exception as e:
        print(f"デコードエラー: {e}")
        return None

def test_token_validation(token):
    """作成したトークンで認証テスト"""
    print("\n=== トークン認証テスト ===")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # ユーザー情報取得テスト
    try:
        response = requests.get(f"{BASE_URL}/users/me/", headers=headers, timeout=10)
        print(f"ユーザー情報取得 - Status: {response.status_code}")
        print(f"レスポンス: {response.text}")
        
        if response.status_code == 200:
            print("✓ 認証成功")
            return True
        else:
            print("✗ 認証失敗")
            return False
    except Exception as e:
        print(f"リクエストエラー: {e}")
        return False

def test_registration_and_login():
    """ユーザー登録とログインの完全テスト"""
    print("\n=== 完全認証フローテスト ===")
    
    # テストユーザーデータ
    test_email = "debug_test@example.com"
    test_password = "debugtest123"
    
    # 1. ユーザー登録
    print("1. ユーザー登録テスト...")
    user_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        reg_response = requests.post(f"{BASE_URL}/users/", json=user_data, timeout=10)
        print(f"登録レスポンス - Status: {reg_response.status_code}")
        print(f"登録レスポンス - Body: {reg_response.text}")
        
        if reg_response.status_code not in [200, 201, 400]:  # 400は既存ユーザーエラー
            print("✗ 登録失敗")
            return None
    except Exception as e:
        print(f"登録リクエストエラー: {e}")
        return None
    
    # 2. ログイン
    print("\n2. ログインテスト...")
    login_data = {
        "username": test_email,
        "password": test_password
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/token", data=login_data, timeout=10)
        print(f"ログインレスポンス - Status: {login_response.status_code}")
        print(f"ログインレスポンス - Body: {login_response.text}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data.get("access_token")
            print(f"✓ ログイン成功、トークン取得: {access_token[:50]}...")
            return access_token
        else:
            print("✗ ログイン失敗")
            return None
    except Exception as e:
        print(f"ログインリクエストエラー: {e}")
        return None

def main():
    print("FastAPI認証システム詳細デバッグ")
    print("======================================")
    
    # 1. データベース状態確認
    has_users = check_database()
    
    # 2. サーバー接続確認
    if not test_server_connection():
        print("\n❌ サーバーが起動していません。以下のコマンドでサーバーを起動してください:")
        print("python -m uvicorn main:app --reload --port 8001")
        return
    
    # 3. 完全な認証フローテスト
    access_token = test_registration_and_login()
    
    if access_token:
        # 4. 保護されたエンドポイントのテスト
        print("\n3. 保護されたエンドポイントテスト...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # モデル一覧取得
        try:
            models_response = requests.get(f"{BASE_URL}/models/", headers=headers, timeout=10)
            print(f"モデル一覧 - Status: {models_response.status_code}")
            print(f"モデル一覧 - Body: {models_response.text}")
            
            # 背景画像一覧取得
            bg_response = requests.get(f"{BASE_URL}/backgrounds/", headers=headers, timeout=10)
            print(f"背景一覧 - Status: {bg_response.status_code}")
            print(f"背景一覧 - Body: {bg_response.text}")
            
            if models_response.status_code == 200 and bg_response.status_code == 200:
                print("\n✅ 全ての認証テストが成功しました！")
                print("401エラーは解決されています。")
            else:
                print("\n⚠️  まだ認証問題があります。")
                
        except Exception as e:
            print(f"保護されたエンドポイントテストエラー: {e}")
    
    # 5. 手動トークンテスト（デバッグ用）
    if not has_users:
        print("\n4. 手動トークンテスト...")
        manual_token = create_test_token()
        if manual_token:
            test_token_validation(manual_token)

if __name__ == "__main__":
    main()
