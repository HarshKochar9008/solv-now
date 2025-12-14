from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    linkedin_id = Column(String, index=True)
    profile_picture = Column(String)
    description = Column(Text)
    website = Column(String)
    industry = Column(String, index=True)
    total_followers = Column(BigInteger, default=0)
    head_count = Column(Integer)
    specialities = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    posts = relationship("Post", back_populates="page", cascade="all, delete-orphan")
    employees = relationship("Employee", back_populates="page", cascade="all, delete-orphan")

class SocialMediaUser(Base):
    __tablename__ = "social_media_users"
    
    id = Column(Integer, primary_key=True, index=True)
    linkedin_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    profile_url = Column(String)
    profile_picture = Column(String)
    headline = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    comments = relationship("Comment", back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    linkedin_post_id = Column(String, unique=True, index=True)
    content = Column(Text)
    post_url = Column(String)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    posted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    page = relationship("Page", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("social_media_users.id"))
    linkedin_comment_id = Column(String, unique=True, index=True)
    content = Column(Text)
    likes_count = Column(Integer, default=0)
    posted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    post = relationship("Post", back_populates="comments")
    author = relationship("SocialMediaUser", back_populates="comments")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False)
    name = Column(String, nullable=False)
    profile_url = Column(String)
    profile_picture = Column(String)
    headline = Column(String)
    position = Column(String)
    linkedin_id = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    page = relationship("Page", back_populates="employees")

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_address = Column(String, unique=True, index=True, nullable=False)
    public_key = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    last_connected_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

