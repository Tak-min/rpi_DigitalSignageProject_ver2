#!/usr/bin/env python3
"""
統合されたFastAPIバックエンド
すべてのモデル、スキーマ、CRUD、認証機能を含む単一ファイル
"""

import os
import uuid
import warnings
from typing import List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import traceback

# FastAPI関連のインポート
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

# SQLAlchemy関連のインポート
from sqlalchemy import create_engine, Boolean, Column, ForeignKey, Integer, String, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func

# Pydantic関連のインポート
from pydantic import BaseModel, EmailStr

# セキュリティ関連のインポート
from passlib.context import CryptContext
from jose import JWTError, jwt

# =======================
# データベース設定
# =======================

# SQLiteデータベースのURLを指定
SQLALCHEMY_DATABASE_URL = "sqlite:///./database_new.db"

# エンジンを作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# セッションのローカルクラスを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスを作成
Base = declarative_base()

# データベースのセッションを取得する関数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =======================
# SQLAlchemyモデル
# =======================

# ユーザーモデル
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        {'extend_existing': True},
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=False)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # リレーションシップの定義
    vrm_models = relationship("VRMModel", back_populates="user", cascade="all, delete-orphan")
    vrm_animations = relationship("VRMAnimation", back_populates="user", cascade="all, delete-orphan")
    backgrounds = relationship("Background", back_populates="user", cascade="all, delete-orphan")

# VRMモデル
class VRMModel(Base):
    __tablename__ = "vrm_models"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    vrm_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="vrm_models")
    animations = relationship("VRMAnimation", back_populates="model", cascade="all, delete-orphan")

# VRMアニメーション
class VRMAnimation(Base):
    __tablename__ = "vrm_animations"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    anim_name = Column(String, nullable=False)
    vrma_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    model_id = Column(Integer, ForeignKey("vrm_models.id"))

    user = relationship("User", back_populates="vrm_animations")
    model = relationship("VRMModel", back_populates="animations")

# 背景画像モデル
class Background(Base):
    """背景画像モデル"""
    __tablename__ = "backgrounds"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # リレーションシップ
    user = relationship("User", back_populates="backgrounds")

# =======================
# Pydanticスキーマ
# =======================

# ベースモデル
class UserBase(BaseModel):
    email: EmailStr

# ユーザー登録用モデル
class UserCreate(UserBase):
    password: str

# アニメーションの表示用モデル
class VRMAnimationBase(BaseModel):
    id: int
    anim_name: str
    vrma_path: str

    class Config:
        from_attributes = True

# モデルの表示用モデル
class VRMModelBase(BaseModel):
    id: int
    name: str
    vrm_path: str
    animations: List[VRMAnimationBase] = []

    class Config:
        from_attributes = True

# ユーザー情報の表示用モデル
class UserSchema(UserBase):
    id: int
    is_active: bool
    vrm_models: List[VRMModelBase] = []

    class Config:
        from_attributes = True

# トークン用モデル
class Token(BaseModel):
    access_token: str
    token_type: str

# トークンデータ用モデル
class TokenData(BaseModel):
    email: Optional[str] = None

# アニメーション作成用モデル
class VRMAnimationCreate(BaseModel):
    anim_name: str

# モデル作成用モデル
class VRMModelCreate(BaseModel):
    name: str

# 背景画像のベースモデル
class BackgroundBase(BaseModel):
    id: int
    filename: str
    path: str

    class Config:
        from_attributes = True

# 背景画像の作成用モデル
class BackgroundCreate(BaseModel):
    filename: str
    path: str
    user_id: int

# =======================
# 認証設定
# =======================

# JWT設定
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24時間

# passlib警告抑制（bcrypt）
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")

# パスワードハッシュ用のコンテキスト
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2のスキーマを設定（トークンエンドポイントを指定）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# =======================
# 認証関数
# =======================

# パスワードをハッシュ化
def get_password_hash(password):
    return pwd_context.hash(password)

# パスワードの検証
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ユーザー認証
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# アクセストークンの生成
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 現在のユーザーを取得
async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# アクティブユーザーを確認
async def get_current_active_user(current_user: UserSchema = Depends(get_current_user)):
    return current_user

# =======================
# CRUD関数
# =======================

# ユーザーをメールアドレスで取得
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# ユーザー作成
def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ユーザーのモデル一覧を取得
def get_vrm_models(db: Session, user_id: int):
    return db.query(VRMModel).filter(VRMModel.user_id == user_id).all()

# VRMモデルを作成する関数
async def create_vrm_model(db: Session, name: str, vrm_file: UploadFile, user_id: int):
    # ユーザーごとのディレクトリを作成
    user_dir = os.path.join("uploads", str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # ファイル名を一意にする
    file_uuid = str(uuid.uuid4())
    file_extension = os.path.splitext(vrm_file.filename)[1]
    file_name = f"{file_uuid}{file_extension}"
    file_path = os.path.join(user_dir, file_name)
    
    # ファイルを保存
    with open(file_path, "wb") as buffer:
        content = await vrm_file.read()
        buffer.write(content)
    
    # URLパスとして使えるように \ を / に置換
    url_path = "/" + file_path.replace("\\", "/")
    
    # データベースに登録
    db_vrm = VRMModel(name=name, vrm_path=url_path, user_id=user_id)
    db.add(db_vrm)
    db.commit()
    db.refresh(db_vrm)
    return db_vrm

# VRMアニメーションを作成
async def create_vrm_animation(db: Session, anim_name: str, vrma_file: UploadFile, model_id: int, user_id: int):
    # ユーザーごとのディレクトリを作成
    user_dir = os.path.join("uploads", str(user_id), "animations")
    os.makedirs(user_dir, exist_ok=True)
    
    # ファイル名を一意にする
    file_uuid = str(uuid.uuid4())
    file_extension = os.path.splitext(vrma_file.filename)[1]
    file_name = f"{file_uuid}{file_extension}"
    file_path = os.path.join(user_dir, file_name)
    
    # ファイルを保存
    with open(file_path, "wb") as buffer:
        content = await vrma_file.read()
        buffer.write(content)
    
    # URLパスとして使えるように \ を / に置換
    url_path = "/" + file_path.replace("\\", "/")
    
    # データベースに登録
    db_animation = VRMAnimation(
        anim_name=anim_name,
        vrma_path=url_path,
        model_id=model_id,
        user_id=user_id
    )
    db.add(db_animation)
    db.commit()
    db.refresh(db_animation)
    return db_animation

# 背景画像をデータベースに保存する関数
def create_background(db: Session, filename: str, path: str, user_id: int):
    """背景画像情報をデータベースに保存する"""
    db_background = Background(
        filename=filename,
        path=path,
        user_id=user_id
    )
    db.add(db_background)
    db.commit()
    db.refresh(db_background)
    return db_background

# ユーザーの背景画像一覧を取得する関数
def get_backgrounds(db: Session, user_id: int):
    """ユーザーの背景画像一覧を取得する"""
    return db.query(Background).filter(Background.user_id == user_id).all()

# 特定の背景画像取得
def get_background(db: Session, background_id: int):
    return db.query(Background).filter(Background.id == background_id).first()

# 背景画像削除
def delete_background(db: Session, background_id: int):
    db_background = get_background(db, background_id)
    if db_background:
        # ファイルシステムからも削除（先頭の / を削除して相対パスに変換）
        file_path = db_background.path.lstrip('/')
        if os.path.exists(file_path):
            os.remove(file_path)
        # データベースから削除
        db.delete(db_background)
        db.commit()
        return True
    return False

# =======================
# 初期化関数
# =======================

# 必須のディレクトリを先に作成
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/backgrounds", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/uploads/backgrounds", exist_ok=True)
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

# データベースの初期化
def init_db():
    inspector = inspect(engine)
    # テーブルが存在しない場合のみ作成
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
    else:
        print("データベースは既に初期化されています。テーブルの再作成はスキップします。")

# 初期化関数を呼び出す
init_db()

# =======================
# FastAPIアプリケーション
# =======================

# FastAPIアプリケーションの作成
app = FastAPI()

# 静的ファイルの設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# アップロードディレクトリも静的ファイルとしてマウント
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# テンプレートディレクトリの設定
templates = Jinja2Templates(directory="templates")

# =======================
# エンドポイント
# =======================

# ルートパス
@app.get("/")
def read_index(request: Request): 
    return templates.TemplateResponse("index.html", {"request": request})

# トークン取得エンドポイント（ログイン）
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ユーザー登録エンドポイント
@app.post("/users/", response_model=UserSchema)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, user=user)

# 現在のユーザー情報取得エンドポイント
@app.get("/users/me/", response_model=UserSchema)
async def read_users_me(current_user: UserSchema = Depends(get_current_active_user)):
    return current_user

# モデル一覧取得エンドポイント
@app.get("/models/", response_model=List[VRMModelBase])
def get_models(current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(get_db)):
    models = get_vrm_models(db, user_id=current_user.id)
    return models

# モデルとアニメーションのアップロードエンドポイント
@app.post("/upload/")
async def upload_model(
    name: str = Form(...),
    vrm_file: UploadFile = File(...),
    vrma_files: List[UploadFile] = File([]),
    current_user: UserSchema = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # ユーザーごとのディレクトリを作成
        user_dir = os.path.join("uploads", str(current_user.id))
        anim_dir = os.path.join(user_dir, "animations")
        os.makedirs(user_dir, exist_ok=True)
        os.makedirs(anim_dir, exist_ok=True)

        # VRMモデルを保存
        model = await create_vrm_model(db, name, vrm_file, current_user.id)
        
        # アニメーションファイルがある場合、それぞれ保存
        animations = []
        if vrma_files:
            for vrma_file in vrma_files:
                if vrma_file.filename:
                    # ファイル名からアニメーション名を抽出（拡張子を除く）
                    anim_name = Path(vrma_file.filename).stem
                    animation = await create_vrm_animation(
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
@app.post("/upload-background/", response_model=BackgroundBase)
async def upload_background(
    background_file: UploadFile = File(...),
    current_user: UserSchema = Depends(get_current_active_user),
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
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # ファイルを保存
        with open(file_path, "wb") as buffer:
            content = await background_file.read()
            buffer.write(content)
            
        # データベースに背景画像情報を保存
        # URLパスとして使えるように \ を / に置換
        url_path = "/" + file_path.replace("\\", "/")
        background = create_background(
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
        error_details = traceback.format_exc()
        print(f"Background upload error: {str(e)}\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"背景画像のアップロードに失敗しました: {str(e)}"
        )

# 背景画像一覧取得エンドポイント
@app.get("/backgrounds/", response_model=List[BackgroundBase])
def get_backgrounds_endpoint(current_user: UserSchema = Depends(get_current_active_user), db: Session = Depends(get_db)):
    backgrounds = get_backgrounds(db, user_id=current_user.id)
    return backgrounds

# デバッグ用エンドポイント
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
    
    return {"status": "success", "routes": routes_info}

# シンプルなテスト用エンドポイント
@app.get("/hello")
def hello():
    """簡単なテスト用エンドポイント"""
    return {"message": "Hello World! デバッグエンドポイントは正常に動作しています。"}

# =======================
# サーバー起動
# =======================

# サーバー起動コード（本番環境ではGunicornを使用）
if __name__ == "__main__":
    import uvicorn
    print("🚀 FastAPIサーバーを起動しています...")
    print("📍 URL: http://localhost:8000")
    print("📖 API ドキュメント: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
