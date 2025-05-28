#!/usr/bin/env python3
"""
簡単なサーバー接続テスト
"""
import requests
import time

def test_server_connection():
    """サーバーへの接続テスト"""
    base_url = "http://localhost:8001"
    
    print("🔍 サーバー接続テストを実行中...")
    
    try:
        print("1. ルートページへのアクセステスト...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ステータス: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ サーバーは正常に動作しています")
            
            # APIエンドポイントのテスト
            print("\n2. APIエンドポイントテスト...")
            
            # モデル一覧エンドポイント（認証なしでアクセス）
            print("   - /models/ エンドポイント...")
            models_response = requests.get(f"{base_url}/models/", timeout=5)
            print(f"     ステータス: {models_response.status_code}")
            
            if models_response.status_code == 401:
                print("     ✅ 認証エラー（正常な動作）")
            elif models_response.status_code == 500:
                print("     ❌ 500エラー - まだ修正が必要です")
                print(f"     エラー詳細: {models_response.text[:300]}...")
            else:
                print(f"     ⚠️ 予期しないステータス: {models_response.status_code}")
            
            # 背景画像一覧エンドポイント
            print("   - /backgrounds/ エンドポイント...")
            bg_response = requests.get(f"{base_url}/backgrounds/", timeout=5)
            print(f"     ステータス: {bg_response.status_code}")
            
            if bg_response.status_code == 401:
                print("     ✅ 認証エラー（正常な動作）")
            elif bg_response.status_code == 500:
                print("     ❌ 500エラー - まだ修正が必要です")
                print(f"     エラー詳細: {bg_response.text[:300]}...")
            else:
                print(f"     ⚠️ 予期しないステータス: {bg_response.status_code}")
                
        else:
            print(f"   ❌ サーバーエラー: {response.status_code}")
            print(f"   詳細: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ サーバーに接続できません")
        print("   💡 サーバーが起動していない可能性があります")
        print("   🚀 次のコマンドでサーバーを起動してください:")
        print("       python main.py")
    except Exception as e:
        print(f"   ❌ テストエラー: {e}")

if __name__ == "__main__":
    test_server_connection()
