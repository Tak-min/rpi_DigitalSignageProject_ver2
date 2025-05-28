from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

# ユーザーモデル
class User(Base):
    __tablename__ = "users"
    # テーブルとインデックスの両方を既存のものに拡張
    __table_args__ = (
        {'extend_existing': True},
    )

    id = Column(Integer, primary_key=True, index=True)
    # unique=Trueのままにするがindex=Falseに変更（既にインデックスがあるため）
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