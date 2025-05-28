import os
import sys

# データベースファイルのパスを指定
DB_FILE = "database.db"  # database.pyで指定されているファイル名

def reset_database():
    """データベースをリセットする"""
    # ファイルの存在を確認
    if os.path.exists(DB_FILE):
        print(f"既存のデータベース '{DB_FILE}' を削除します...")
        os.remove(DB_FILE)
        print("削除完了")
    else:
        print(f"データベースファイル '{DB_FILE}' は存在しません。新規作成します。")
      # データベースを再作成
    print("データベースを初期化しています...")
    try:
        import models  # modelsをインポートしてテーブル定義を読み込む
        from database import Base, engine
        Base.metadata.create_all(bind=engine)
        print("データベースの初期化が完了しました!")
    except Exception as e:
        print(f"データベースの初期化中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 確認プロンプト
    confirm = input("警告: データベースをリセットすると、すべてのデータが失われます。続行しますか？ (y/n): ")
    
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("リセットを中止しました。")
        sys.exit(0)
