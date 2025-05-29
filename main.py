import os
from typing import List
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from pathlib import Path
import shutil
import traceback

import crud
import auth
import schemas
import models  # SQLAlchemyモデルをインポート
from database import engine, Base, get_db

# 必須のディレクトリを先に作成
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/backgrounds", exist_ok=True)  # 背景画像用のディレクトリを作成
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/uploads/backgrounds", exist_ok=True)  # 静的ファイル用の背景画像ディレクトリ
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# デフォルト背景画像の確認と作成（存在しない場合）
default_bg_path = "static/uploads/backgrounds/default.jpg"
if not os.path.exists(default_bg_path):
    # シンプルな単色背景画像を作成
    try:
        from PIL import Image
        img = Image.new('RGB', (800, 600), color = (240, 240, 240))
        img.save(default_bg_path)
        print(f"デフォルト背景画像を作成しました: {default_bg_path}")
    except ImportError:
        print("警告: Pillowライブラリがインストールされていないため、デフォルト背景画像を作成できません。")
        print("pip install Pillowを実行してPillowをインストールするか、手動で背景画像を配置してください。")
        # シンプルな空ファイルを作成（応急処置）
        with open(default_bg_path, "wb") as f:
            # 最小限の有効なJPEG画像データ
            f.write(b'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01\x01\x01\x00\x48\x00\x48\x00\x00\xff\xdb\x00\x43\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xdb\x00\x43\x01\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01\x22\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x15\x00\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xbf\x80\x01\xff\xd9')

# データベースの初期化（修正版）
def init_db():
    inspector = inspect(engine)
    # テーブルが存在しない場合のみ作成
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
    else:
        print("データベースは既に初期化されています。テーブルの再作成はスキップします。")

# 初期化関数を呼び出す
init_db()

# FastAPIアプリケーションの作成
app = FastAPI()

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# アップロードディレクトリも静的ファイルとしてマウント
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# テンプレートディレクトリの設定
templates = Jinja2Templates(directory="templates")

# ルートパス
@app.get("/")
def read_index(request: Request): 
    return templates.TemplateResponse("index.html", {"request": request})

# トークン取得エンドポイント（ログイン）
@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ユーザー登録エンドポイント
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

# 現在のユーザー情報取得エンドポイント
@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user

# モデル一覧取得エンドポイント
@app.get("/models/", response_model=List[schemas.VRMModelBase])
def get_models(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    models = crud.get_vrm_models(db, user_id=current_user.id)
    return models

# モデルとアニメーションのアップロードエンドポイント
@app.post("/upload/")
async def upload_model(
    name: str = Form(...),
    vrm_file: UploadFile = File(...),
    vrma_files: List[UploadFile] = File([]),  # 空のリストをデフォルト値に設定
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # ユーザーごとのディレクトリを作成
        user_dir = os.path.join("uploads", str(current_user.id))
        anim_dir = os.path.join(user_dir, "animations")
        os.makedirs(user_dir, exist_ok=True)
        os.makedirs(anim_dir, exist_ok=True)

        # VRMモデルを保存
        model = await crud.create_vrm_model(db, name, vrm_file, current_user.id)
        
        # アニメーションファイルがある場合、それぞれ保存
        animations = []
        if vrma_files:  # リストが空でない場合のみ処理
            for vrma_file in vrma_files:
                if vrma_file.filename:  # ファイル名が空でないことを確認
                    # ファイル名からアニメーション名を抽出（拡張子を除く）
                    anim_name = Path(vrma_file.filename).stem
                    animation = await crud.create_vrm_animation(
                        db, anim_name, vrma_file, model.id, current_user.id
                    )
                    if animation:
                        animations.append(animation)
        # モデルとアニメーション情報を返す
        return {
            "model": {
                "id": model.id,
                "name": model.name,
                "vrm_path": model.vrm_path
            },
            "animations": [
                {
                "id": anim.id,
                "name": anim.anim_name,
                "path": anim.vrma_path
            } for anim in animations
            ]
        }
    except Exception as e:
        # 詳細なエラー情報を記録
        error_details = traceback.format_exc()
        print(f"Upload error: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload model: {str(e)}"
        )

# 背景画像アップロードエンドポイント
@app.post("/upload-background/", response_model=schemas.BackgroundBase)
async def upload_background(
    background_file: UploadFile = File(...),
    current_user: schemas.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # ファイル名から拡張子を抽出して、サポートしている画像形式かをチェック
        file_ext = Path(background_file.filename).suffix.lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="サポートされていないファイル形式です。JPG、PNG、またはGIF画像をアップロードしてください。"
            )
            
        # ユーザーごとのディレクトリを作成
        user_dir = os.path.join("uploads", str(current_user.id), "backgrounds")
        os.makedirs(user_dir, exist_ok=True)
            
        # 一意のファイル名を生成
        import uuid
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # ファイルを保存
        with open(file_path, "wb") as buffer:
            content = await background_file.read()
            buffer.write(content)
            
        # データベースに背景画像情報を保存
        # URLパスとして使えるように \ を / に置換
        url_path = "/" + file_path.replace("\\", "/")
        background = crud.create_background(
            db, 
            filename=background_file.filename,
            path=url_path,
            user_id=current_user.id
        )
            
        return {
            "id": background.id,
            "filename": background.filename,
            "path": background.path
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Background upload error: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"背景画像のアップロードに失敗しました: {str(e)}"
        )

# 背景画像一覧取得エンドポイント
@app.get("/backgrounds/", response_model=List[schemas.BackgroundBase])
def get_backgrounds(current_user: schemas.User = Depends(auth.get_current_active_user), db: Session = Depends(get_db)):
    backgrounds = crud.get_backgrounds(db, user_id=current_user.id)
    return backgrounds

# デバッグ用エンドポイント - 修正版
@app.get("/debug/routes/", response_class=JSONResponse)
async def get_routes():
    """アプリケーションの全ルートをJSONとして返す（デバッグ用）"""
    routes_info = []
    for route in app.routes:
        methods = list(route.methods) if hasattr(route, "methods") else []
        routes_info.append({
            "path": route.path,
            "name": route.name,
            "methods": methods
        })
    
    # 結果をJSON形式で返す
    return {"status": "success", "routes": routes_info}

# もっとシンプルなデバッグエンドポイントも追加
@app.get("/hello")
def hello():
    """簡単なテスト用エンドポイント"""
    return {"message": "Hello World! デバッグエンドポイントは正常に動作しています。"}

# サーバー起動コード（本番環境ではGunicornを使用）
if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPIサーバーを起動しています...")
    print("📍 URL: http://localhost:8000")
    print("📖 API ドキュメント: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
