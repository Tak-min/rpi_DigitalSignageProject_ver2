#!/usr/bin/env python3
"""
包括的なサーバーテストとスタートアップスクリプト
"""
import subprocess
import time
import requests
import threading
import sys
import os
from pathlib import Path

class ServerTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.server_process = None
        
    def start_server(self):
        """サーバーを起動する"""
        print("🚀 FastAPIサーバーを起動しています...")
        try:
            # サーバーを別プロセスで起動
            self.server_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # サーバーが起動するまで待機
            for i in range(30):  # 30秒まで待機
                try:
                    response = requests.get(f"{self.base_url}/", timeout=2)
                    if response.status_code == 200:
                        print(f"✅ サーバーが起動しました（{i+1}秒後）")
                        return True
                except:
                    time.sleep(1)
                    print(f"⏳ サーバー起動待機中... ({i+1}/30)")
            
            print("❌ サーバーの起動がタイムアウトしました")
            return False
            
        except Exception as e:
            print(f"❌ サーバー起動エラー: {e}")
            return False
    
    def test_endpoints(self):
        """各エンドポイントをテストする"""
        print("\n🔍 エンドポイントテストを開始...")
        
        tests = [
            {
                "name": "ルートページ",
                "url": "/",
                "method": "GET",
                "expected_status": [200]
            },
            {
                "name": "APIドキュメント",
                "url": "/docs",
                "method": "GET", 
                "expected_status": [200]
            },
            {
                "name": "モデル一覧（認証なし）",
                "url": "/models/",
                "method": "GET",
                "expected_status": [401, 403]  # 認証エラーが正常
            },
            {
                "name": "背景画像一覧（認証なし）",
                "url": "/backgrounds/",
                "method": "GET",
                "expected_status": [401, 403]  # 認証エラーが正常
            }
        ]
        
        results = {}
        
        for test in tests:
            try:
                print(f"\n📋 テスト: {test['name']}")
                print(f"   URL: {test['url']}")
                
                response = requests.get(f"{self.base_url}{test['url']}", timeout=5)
                status = response.status_code
                
                print(f"   ステータス: {status}")
                
                if status in test['expected_status']:
                    print(f"   ✅ 正常: 期待されたステータス {test['expected_status']} を受信")
                    results[test['name']] = "SUCCESS"
                elif status == 500:
                    print(f"   ❌ 500エラー: 内部サーバーエラーが発生")
                    print(f"   詳細: {response.text[:200]}...")
                    results[test['name']] = "500_ERROR"
                else:
                    print(f"   ⚠️  予期しないステータス: {status}")
                    results[test['name']] = f"UNEXPECTED_{status}"
                    
            except requests.exceptions.RequestException as e:
                print(f"   ❌ 接続エラー: {e}")
                results[test['name']] = "CONNECTION_ERROR"
            except Exception as e:
                print(f"   ❌ テストエラー: {e}")
                results[test['name']] = "TEST_ERROR"
        
        return results
    
    def check_files(self):
        """重要なファイルの存在確認"""
        print("\n📁 ファイル存在確認...")
        
        files_to_check = [
            "main.py",
            "database.py", 
            "models.py",
            "auth.py",
            "crud.py",
            "schemas.py",
            "database_new.db",
            "static/js/main.js",
            "templates/index.html"
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path} が見つかりません")
    
    def stop_server(self):
        """サーバーを停止する"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("\n🛑 サーバーを停止しました")
            except:
                self.server_process.kill()
                print("\n🛑 サーバーを強制終了しました")
    
    def run_full_test(self):
        """完全なテストスイートを実行"""
        print("=" * 60)
        print("🧪 FastAPI 3Dレンダリングアプリケーション テストスイート")
        print("=" * 60)
        
        # ファイル確認
        self.check_files()
        
        # サーバー起動
        if not self.start_server():
            print("\n❌ テスト中止: サーバーが起動できませんでした")
            return
        
        try:
            # エンドポイントテスト
            results = self.test_endpoints()
            
            # 結果まとめ
            print("\n" + "=" * 50)
            print("📊 テスト結果まとめ")
            print("=" * 50)
            
            success_count = sum(1 for result in results.values() if result == "SUCCESS")
            total_tests = len(results)
            
            for test_name, result in results.items():
                status_icon = "✅" if result == "SUCCESS" else "❌"
                print(f"{status_icon} {test_name}: {result}")
            
            print(f"\n📈 成功率: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
            
            # 500エラーの確認
            error_500_tests = [name for name, result in results.items() if result == "500_ERROR"]
            if error_500_tests:
                print(f"\n⚠️  500エラーが発生したエンドポイント:")
                for test in error_500_tests:
                    print(f"   - {test}")
                print("\n💡 これらのエラーを修正する必要があります")
            else:
                print("\n🎉 500エラーは検出されませんでした！")
                
        finally:
            self.stop_server()

if __name__ == "__main__":
    # カレントディレクトリの確認
    current_dir = os.getcwd()
    expected_dir = "display_project"
    
    if not current_dir.endswith(expected_dir):
        print(f"❌ 正しいディレクトリで実行してください")
        print(f"現在: {current_dir}")
        print(f"期待: .../{expected_dir}")
        sys.exit(1)
    
    tester = ServerTester()
    tester.run_full_test()
