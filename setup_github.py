#!/usr/bin/env python3
"""
GitHub リポジトリセットアップスクリプト
"""
import os
import subprocess
import sys

def run_command(command, description):
    """コマンドを実行して結果を表示"""
    print(f"\n🔧 {description}")
    print(f"実行中: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ 成功: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ エラー: {e}")
        if e.stderr:
            print(f"詳細: {e.stderr.strip()}")
        return False

def setup_git_repository():
    """Gitリポジトリのセットアップ"""
    print("=" * 60)
    print("🚀 GitHub リポジトリセットアップ")
    print("=" * 60)
    
    # 現在のディレクトリを確認
    current_dir = os.getcwd()
    if not current_dir.endswith("display_project"):
        print("❌ display_projectディレクトリで実行してください")
        sys.exit(1)
    
    # Git初期化
    if not os.path.exists('.git'):
        run_command("git init", "Gitリポジトリを初期化")
        
    # ファイルをステージング
    run_command("git add .", "ファイルをステージング")
    
    # 初回コミット
    commit_message = "Initial commit: 3D VRM Model Viewer & Animation System"
    run_command(f'git commit -m "{commit_message}"', "初回コミット")
    
    # メインブランチ名を設定
    run_command("git branch -M main", "メインブランチをmainに設定")
    
    print("\n" + "=" * 60)
    print("✅ ローカルリポジトリのセットアップが完了しました！")
    print("=" * 60)
    
    # print("\n📝 次のステップ:")
    # print("1. GitHubでリポジトリを作成:")
    # print("   https://github.com/new")
    print("\n2. リモートリポジトリを追加:")
    print("   git remote add origin https://github.com/Tak-min/rpi_DigitalSignageProject_ver2.git")
    print("\n3. リポジトリにプッシュ:")
    print("   git push -u origin main")
    
    print("\n🔍 除外されるファイル:")
    excluded_files = [
        "*.db (データベースファイル)",
        "__pycache__/ (Pythonキャッシュ)",
        "uploads/ (アップロードファイル)",
        ".env (環境変数)",
        "*.log (ログファイル)"
    ]
    for file in excluded_files:
        print(f"   ✓ {file}")
    
    print("\n💡 セキュリティヒント:")
    print("   - auth.pyのSECRET_KEYを本番環境では必ず変更してください")
    print("   - .env.exampleを参考に環境変数を設定してください")
    print("   - requirements.txtでパッケージバージョンを管理してください")

def check_gitignore():
    """gitignoreファイルの確認"""
    if os.path.exists('.gitignore'):
        print("\n✅ .gitignoreファイルが存在します")
        with open('.gitignore', 'r', encoding='utf-8') as f:
            content = f.read()
            if '*.db' in content and '__pycache__' in content:
                print("✅ 重要なファイルが除外設定されています")
            else:
                print("⚠️ .gitignoreの設定を確認してください")
    else:
        print("❌ .gitignoreファイルがありません")

def check_required_files():
    """必要なファイルの存在確認"""
    required_files = [
        'README.md',
        'requirements.txt',
        '.gitignore',
        '.env.example',
        'main.py'
    ]
    
    print("\n📋 必要ファイルチェック:")
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} が見つかりません")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("🔍 事前チェック...")
    check_gitignore()
    
    if check_required_files():
        setup_git_repository()
    else:
        print("\n❌ 必要ファイルが不足しています。先にファイルを作成してください。")
        sys.exit(1)
