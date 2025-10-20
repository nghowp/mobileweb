from flask import current_app
from flaskproject.models import Category, Product


def load_categories():
    return Category.query.all()


def load_products(cate_id=None, kw=None, from_price=None, to_price=None, page=1):
    products = Product.query.filter(Product.active.is_(True))
    if cate_id:
        try:
            cid = int(cate_id)
            products = products.filter(Product.category_id == cid)
        except ValueError:
            pass

    if kw:
        products = products.filter(Product.name.contains(kw))

    if from_price:
        try:
            fp = float(from_price)
            products = products.filter(Product.price >= fp)
        except ValueError:
            pass

    if to_price:
        try:
            tp = float(to_price)
            products = products.filter(Product.price <= tp)
        except ValueError:
            pass

    page_size = current_app.config["PAGE_SIZE"]
    start = (page - 1) * page_size
    end = start + page_size
    # select * from products limit 4 offset 0
    return products.slice(start, end).all()


def count_product():
    return Product.query.filter(Product.active.__eq__(True)).count()
