from flaskproject import db
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class Category(BaseModel):
    __tablename__ = "category"
    name = Column(String(25), nullable=False)
    products = relationship("Product", backref="category", lazy="select")

    def __str__(self):
        return self.name


class Product(BaseModel):
    __tablename__ = "product"
    name = Column(String(50), nullable=False)
    description = Column(Text)
    price = Column(Float, default=0)
    screen = Column(Text)  # Màn hình
    operating = Column(Text)  # Hệ điều hành
    camera_f = Column(Text)  # Camera trước
    camera_a = Column(Text)  # Camera sau
    CPU = Column(Text)
    RAM = Column(Text)
    store = Column(Text)  # Bộ nhớ trong
    battery = Column(Text)  # Thời lượng pin
    image = Column(String(100))
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, nullable=False, default=func.now())
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False, default=1)

    def __str__(self):
        return self.name
