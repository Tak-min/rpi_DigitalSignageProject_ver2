import os
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile
import models
import schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードハッシュ化関数
def get_password_hash(password):
    return pwd_context.hash(password)

# ユーザーをメールアドレスで取得
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# ユーザー作成
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ユーザーのモデル一覧を取得
def get_vrm_models(db: Session, user_id: int):
    return db.query(models.VRMModel).filter(models.VRMModel.user_id == user_id).all()

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
    db_vrm = models.VRMModel(name=name, vrm_path=url_path, user_id=user_id)
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
    db_animation = models.VRMAnimation(
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
    db_background = models.Background(
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
    return db.query(models.Background).filter(models.Background.user_id == user_id).all()

# 特定の背景画像取得
def get_background(db: Session, background_id: int):
    return db.query(models.Background).filter(models.Background.id == background_id).first()

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
