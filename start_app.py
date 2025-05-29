#!/usr/bin/env python3
"""
サーバー起動と初期化の自動化スクリプト
"""
import os
import sys
import time
import subprocess
import sqlite3
from pathlib import Path

def check_database():
    """データベースの存在確認"""
    db_path = Path("database_new.db")
    if not db_path.exists():
        print("❌ データベースファイルが存在しません")
        return False
    
    try:
        conn = sqlite3.connect('database_new.db')
        cursor = conn.cursor()
        
        # テーブルの存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        required_tables = ['users', 'vrm_models', 'vrm_animations', 'backgrounds']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"❌ 必要なテーブルが不足: {missing_tables}")
            conn.close()
            return False
            
        print(f"✅ データベース確認完了 (テーブル: {len(tables)}個)")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ データベースエラー: {e}")
        return False

def initialize_database():
    """データベースの初期化"""
    print("📦 データベースを初期化中...")
    try:
        result = subprocess.run([sys.executable, "complete_reset.py"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ データベース初期化完了")
            return True
        else:
            print(f"❌ データベース初期化失敗: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ データベース初期化がタイムアウトしました")
        return False
    except Exception as e:
        print(f"❌ データベース初期化エラー: {e}")
        return False

def start_server():
    """サーバーの起動"""
    print("🚀 FastAPIサーバーを起動中...")
    try:
        # サーバーをバックグラウンドで起動
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "main:app", "--reload", "--port", "8001"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # サーバーの起動を少し待つ
        time.sleep(3)
        
        # プロセスが実行中かチェック
        if process.poll() is None:
            print("✅ サーバー起動成功 (PID: {})".format(process.pid))
            print("🌐 http://localhost:8001 でアクセス可能です")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ サーバー起動失敗")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ サーバー起動エラー: {e}")
        return None

def check_server_health():
    """サーバーの健全性チェック"""
    import requests
    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        if response.status_code == 200:
            print("✅ サーバーは正常に応答しています")
            return True
        else:
            print(f"⚠️ サーバーが異常なレスポンス: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ サーバー接続エラー: {e}")
        return False

def create_test_user_if_needed():
    """必要に応じてテストユーザーを作成"""
    try:
        conn = sqlite3.connect('database_new.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        conn.close()
        
        if user_count == 0:
            print("👤 テストユーザーを作成中...")
            import requests
            
            user_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            response = requests.post("http://localhost:8001/users/", json=user_data, timeout=10)
            if response.status_code in [200, 201]:
                print("✅ テストユーザー作成成功")
                print("📧 Email: test@example.com")
                print("🔑 Password: testpassword123")
                return True
            else:
                print(f"⚠️ テストユーザー作成失敗: {response.text}")
                return False
        else:
            print(f"✅ データベースに {user_count} 名のユーザーが存在します")
            return True
    except Exception as e:
        print(f"❌ テストユーザー作成エラー: {e}")
        return False

def main():
    print("FastAPI VRM アプリケーション起動スクリプト")
    print("=" * 50)
    
    # 1. データベースチェック
    if not check_database():
        print("\n🔧 データベースを初期化します...")
        if not initialize_database():
            print("❌ データベースの初期化に失敗しました")
            return 1
    
    # 2. サーバー起動
    server_process = start_server()
    if not server_process:
        print("❌ サーバーの起動に失敗しました")
        return 1
    
    # 3. サーバー健全性チェック
    time.sleep(2)  # サーバーの完全起動を待つ
    if not check_server_health():
        print("❌ サーバーの健全性チェックに失敗しました")
        server_process.terminate()
        return 1
    
    # 4. テストユーザー作成
    if not create_test_user_if_needed():
        print("⚠️ テストユーザーの作成に失敗しましたが、継続します")
    
    print("\n🎉 すべて準備完了！")
    print("=" * 50)
    print("📝 次の手順:")
    print("1. ブラウザで http://localhost:8001 にアクセス")
    print("2. テストユーザーでログイン:")
    print("   - Email: test@example.com")
    print("   - Password: testpassword123")
    print("3. サーバーを停止する場合は Ctrl+C を押してください")
    print()
    
    try:
        # サーバープロセスの監視
        while True:
            if server_process.poll() is not None:
                print("⚠️ サーバープロセスが終了しました")
                break
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止中...")
        server_process.terminate()
        server_process.wait()
        print("✅ サーバーが停止しました")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
