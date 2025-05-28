from typing import List, Optional
from pydantic import BaseModel, EmailStr

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
        from_attributes = True  # 旧: orm_mode = True

# モデルの表示用モデル
class VRMModelBase(BaseModel):
    id: int
    name: str
    vrm_path: str
    animations: List[VRMAnimationBase] = []

    class Config:
        from_attributes = True  # 旧: orm_mode = True

# ユーザー情報の表示用モデル
class User(UserBase):
    id: int
    is_active: bool
    vrm_models: List[VRMModelBase] = []

    class Config:
        from_attributes = True  # 旧: orm_mode = True

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
    # vrma_file はフォームデータで送信されるため、ここでは定義しない

# モデル作成用モデル
class VRMModelCreate(BaseModel):
    name: str
    # vrm_file はフォームデータで送信されるため、ここでは定義しない

# 背景画像のベースモデル
class BackgroundBase(BaseModel):
    id: int
    filename: str
    path: str

    class Config:
        from_attributes = True  # 旧: orm_mode = True

# 背景画像の作成用モデル
class BackgroundCreate(BaseModel):
    filename: str
    path: str
    user_id: int
