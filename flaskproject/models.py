from enum import Enum as UserEnum

from flask_login import UserMixin
from flaskproject import db
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
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
    rating_score = Column(Float, nullable=False, default=0.0)  # Số lượng sao sản phẩm
    rating_count = Column(Integer, nullable=False, default=0)  # Số lượt đánh giá
    sold_count = Column(Integer, nullable=False, default=0)  # Số lượt bán
    image = Column(String(100))
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, nullable=False, default=func.now())
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False, default=1)
    stock_quantity = Column(Integer, nullable=False, default=0)  # Số lượng tồn kho

    receipt_details = relationship("ReceiptDetail", backref="product", lazy="select")
    flash_sale_deal = relationship("FlashSale", back_populates="product", uselist=False)

    def __str__(self):
        return self.name


class FlashSale(BaseModel):
    __tablename__ = "flash_sale"
    min_discount_percent = Column(Float, nullable=False, default=10.0)
    max_discount_percent = Column(Float, nullable=False, default=16.0)
    is_active = Column(Boolean, default=True, nullable=False)
    product_id = Column(Integer, ForeignKey("product.id"), nullable=False, unique=True)
    product = relationship("Product", back_populates="flash_sale_deal")

    def __repr__(self):
        if self.product:
            return f"<FlashSalePool {self.product.name} ({self.min_discount_percent}%-{self.max_discount_percent}%)>"
        return f"<FlashSalePool product_id={self.product_id}>"


class UserRole(UserEnum):
    ADMIN = 1
    USER = 2


class User(BaseModel, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=func.now())
    userrole = Column(Enum(UserRole), default=UserRole.USER)
    receipt = relationship("Receipt", backref="user", lazy="select")

    def __str__(self):
        return self.name


class Receipt(BaseModel):  # Hóa đơn
    created_date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    total_price = Column(Float, nullable=True, default=0)
    status = Column(String(50), nullable=False, default="Đang xử lý")
    customer_name = Column(String(100), nullable=False, default="")  # Tên người nhận
    shipping_phone = Column(String(20), nullable=False, default="")  # SĐT người nhận
    shipping_address = Column(Text, nullable=False, default="")  # Địa chỉ giao hàng
    payment_method = Column(String(50), nullable=False, default="cod")  # Phương thức TT
    details = relationship("ReceiptDetail", backref="receipt", lazy="select")


class ReceiptDetail(db.Model):
    receipt_id = Column(
        Integer, ForeignKey(Receipt.id), nullable=False, primary_key=True
    )
    product_id = Column(
        Integer, ForeignKey(Product.id), nullable=False, primary_key=True
    )
    quantity = Column(Integer, default=0)
    unit_price = Column(Float, default=0)
