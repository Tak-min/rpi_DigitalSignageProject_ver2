#!/usr/bin/env python3
"""
データベースとテストユーザーの完全初期化スクリプト
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのファイルをimport可能にする
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base, get_db
from models import User, VRMModel, VRMAnimation, Background
import auth
import crud
import schemas

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
    
    # テーブルを作成
    Base.metadata.create_all(bind=engine)
    print("新しいデータベース作成完了: database_new.db")
    
    return engine

def create_test_user(engine):
    """テストユーザーの作成"""
    print("\n=== テストユーザー作成 ===")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # テストユーザーデータ
        test_user_data = schemas.UserCreate(
            email="test@example.com",
            password="testpassword123"
        )
        
        # ユーザーが既に存在するかチェック
        existing_user = crud.get_user_by_email(db, email=test_user_data.email)
        if existing_user:
            print(f"ユーザー '{test_user_data.email}' は既に存在します")
        else:
            # 新しいユーザーを作成
            user = crud.create_user(db=db, user=test_user_data)
            print(f"テストユーザー作成成功: {user.email} (ID: {user.id})")
        
        # 全ユーザーの確認
        all_users = db.query(User).all()
        print(f"データベース内の全ユーザー ({len(all_users)}人):")
        for user in all_users:
            print(f"  - ID: {user.id}, Email: {user.email}, Created: {user.created_at}")
            
    except Exception as e:
        print(f"テストユーザー作成エラー: {e}")
        db.rollback()
    finally:
        db.close()

def verify_auth_system():
    """認証システムの検証"""
    print("\n=== 認証システム検証 ===")
    
    # JWTトークンの生成テスト
    test_data = {"sub": "test@example.com"}
    token = auth.create_access_token(data=test_data)
    print(f"JWTトークン生成成功: {token[:50]}...")
    
    # パスワードハッシュのテスト
    test_password = "testpassword123"
    hashed = auth.get_password_hash(test_password)
    print(f"パスワードハッシュ生成成功: {hashed[:50]}...")
    
    # パスワード検証のテスト
    verification = auth.verify_password(test_password, hashed)
    print(f"パスワード検証: {'成功' if verification else '失敗'}")

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
        os.makedirs(directory, exist_ok=True)
        print(f"ディレクトリ作成: {directory}")

def main():
    print("FastAPI認証システム完全初期化")
    print("=====================================")
    
    try:
        # 1. データベースリセット
        engine = reset_database()
        
        # 2. テストユーザー作成
        create_test_user(engine)
        
        # 3. 認証システム検証
        verify_auth_system()
        
        # 4. 必要なディレクトリ作成
        create_uploads_directories()
        
        print("\n✅ 初期化完了！")
        print("\n次の手順:")
        print("1. サーバー起動: python -m uvicorn main:app --reload --port 8001")
        print("2. ブラウザで http://localhost:8001 にアクセス")
        print("3. テストユーザーでログイン:")
        print("   - Email: test@example.com")
        print("   - Password: testpassword123")
        
    except Exception as e:
        print(f"\n❌ 初期化エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
