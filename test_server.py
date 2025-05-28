#!/usr/bin/env python3
"""
サーバーの動作テスト用スクリプト
"""
import requests
import time
import threading
import subprocess
import sys
import os

def test_server_endpoints():
    """サーバーエンドポイントをテストする"""
    base_url = "http://localhost:8000"
    
    print("🔍 サーバーエンドポイントのテストを開始します...")
    
    # 1. ルートエンドポイントのテスト
    try:
        print("\n1. ルートページ ('/') のテスト...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ステータス: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ ルートページは正常です")
        else:
            print(f"   ❌ ルートページでエラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ ルートページの接続エラー: {e}")
        return
    
    # 2. APIエンドポイントのテスト
    endpoints = [
        ("/models/", "GET", "モデル一覧取得"),
        ("/backgrounds/", "GET", "背景画像一覧取得"),
        ("/docs", "GET", "API ドキュメント")
    ]
    
    for endpoint, method, description in endpoints:
        try:
            print(f"\n2. {description} ('{endpoint}') のテスト...")
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            print(f"   ステータス: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {description}は正常です")
            elif response.status_code == 401:
                print(f"   ⚠️ {description}は認証が必要です（正常な動作）")
            elif response.status_code == 500:
                print(f"   ❌ {description}で500エラーが発生しています")
                print(f"   エラー詳細: {response.text[:200]}...")
            else:
                print(f"   ⚠️ {description}で予期しないステータス: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {description}の接続エラー: {e}")

def check_server_status():
    """サーバーが起動しているかチェック"""
    try:
        response = requests.get("http://localhost:8000/", timeout=3)
        return True
    except:
        return False

if __name__ == "__main__":
    print("🚀 FastAPIサーバーテストツール")
    print("=" * 50)
    
    # サーバーが起動しているかチェック
    if check_server_status():
        print("✅ サーバーは既に起動しています")
        test_server_endpoints()
    else:
        print("❌ サーバーが起動していません")
        print("\n📝 サーバーを起動するには:")
        print("   python main.py")
        print("\n🔧 データベースを初期化するには:")
        print("   python init_fresh_db.py")
