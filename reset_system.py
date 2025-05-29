#!/usr/bin/env python3
"""
システム完全リセットスクリプト
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def reset_database():
    """データベースを完全にリセット"""
    print("=== データベースリセット開始 ===")
    
    # 既存のデータベースファイルを削除
    db_files = ['database.db', 'database_new.db', 'database_new_backup.db']
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"削除: {db_file}")
    
    # 新しいデータベースを作成
    SQLALCHEMY_DATABASE_URL = "sqlite:///./database_new.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # main.pyからテーブル定義をインポート
    try:
        from main import Base
        Base.metadata.create_all(bind=engine)
        print("✅ 新しいデータベース作成完了: database_new.db")
        return engine
    except ImportError as e:
        print(f"❌ main.pyからのインポートエラー: {e}")
        print("main.pyファイルが存在し、正しく設定されていることを確認してください")
        return None

def create_test_user(engine):
    """テストユーザーの作成"""
    if not engine:
        print("❌ データベースエンジンが無効です")
        return
        
    print("\n=== テストユーザー作成 ===")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # main.pyから必要なクラスをインポート
        from main import User, get_password_hash
        
        # テストユーザーデータ
        email = "test@example.com"
        password = "testpassword123"
        
        # ユーザーが既に存在するかチェック
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"ユーザー '{email}' は既に存在します")
        else:
            # 新しいユーザーを作成
            hashed_password = get_password_hash(password)
            user = User(
                email=email,
                hashed_password=hashed_password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ テストユーザー作成成功: {user.email} (ID: {user.id})")
        
        # 全ユーザーの確認
        all_users = db.query(User).all()
        print(f"データベース内の全ユーザー ({len(all_users)}人):")
        for user in all_users:
            print(f"  - ID: {user.id}, Email: {user.email}, Created: {user.created_at}")
            
    except Exception as e:
        print(f"❌ テストユーザー作成エラー: {e}")
        db.rollback()
    finally:
        db.close()

def create_uploads_directories():
    """アップロード用ディレクトリの作成"""
    print("\n=== アップロードディレクトリ作成 ===")
    
    directories = [
        "uploads",
        "uploads/backgrounds",
        "static/uploads",
        "static/uploads/backgrounds"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ ディレクトリ作成: {directory}")
        except Exception as e:
            print(f"❌ ディレクトリ作成エラー: {directory} - {e}")

def main():
    print("=" * 50)
    print("🔄 システム完全リセット")
    print("=" * 50)
    
    # main.pyの存在確認
    if not os.path.exists("main.py"):
        print("❌ main.pyが見つかりません。display_projectディレクトリで実行してください")
        sys.exit(1)
    
    try:
        # 1. データベースリセット
        engine = reset_database()
        
        # 2. テストユーザー作成
        create_test_user(engine)
        
        # 3. 必要なディレクトリ作成
        create_uploads_directories()
        
        print("\n" + "=" * 50)
        print("✅ システムリセット完了！")
        print("=" * 50)
        print("\n📝 次の手順:")
        print("1. サーバー起動: python main.py")
        print("2. ブラウザで http://localhost:8000 にアクセス")
        print("3. テストユーザーでログイン:")
        print("   - Email: test@example.com")
        print("   - Password: testpassword123")
        print("\n🧪 テスト実行: python test_auth.py")
        
    except Exception as e:
        print(f"\n❌ リセットエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 確認プロンプト
    confirm = input("⚠️  警告: システムをリセットすると、すべてのデータが失われます。続行しますか？ (y/N): ")
    
    if confirm.lower() == 'y':
        main()
    else:
        print("リセットを中止しました。")
        sys.exit(0)
