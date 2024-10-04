import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from src.storages.postgress.setup import Base
from uuid import uuid4

class RSS_feed(Base):
    __tablename__ = 'rss_feed'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(String(255), nullable=False)

    rss_posts = relationship("Post", back_populates="feed")


class Post(Base):
    __tablename__ = 'rss_posts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    pub_date = Column(DateTime, nullable=False)
    
    # Внешний ключ на RSS_feed
    feed_id = Column(UUID(as_uuid=True), ForeignKey('rss_feed.id'))
    feed = relationship("RSS_feed", back_populates="rss_posts")
