#!/usr/bin/env python3
"""
新しいデータベースを初期化するスクリプト
"""
import os
import sys

# 古いデータベースファイルを別名でバックアップ
old_db = "database_new.db"
backup_db = "database_new_backup.db"

if os.path.exists(old_db):
    print(f"既存のデータベースを {backup_db} としてバックアップします...")
    try:
        if os.path.exists(backup_db):
            os.remove(backup_db)
        os.rename(old_db, backup_db)
        print("バックアップ完了")
    except Exception as e:
        print(f"バックアップエラー: {e}")
        print("手動でデータベースファイルを削除してください")
        sys.exit(1)

# 新しいデータベースを作成
print("新しいデータベースを初期化しています...")
try:
    # modelsを先にインポートしてテーブル定義を読み込む
    import models
    from database import Base, engine
      # すべてのテーブルを作成
    Base.metadata.create_all(bind=engine)
    
    print("✅ データベースの初期化が完了しました!")
    print("📁 新しいデータベースファイル: database_new.db")
    print("📁 バックアップファイル: database_new_backup.db")
    
except Exception as e:
    print(f"❌ データベースの初期化に失敗しました: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
