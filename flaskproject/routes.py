from flask import Blueprint, current_app, render_template, request
from flaskproject import utils

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    css_file = [
        "css/style.css",
        "css/topnav.css",
        "css/header.css",
        "css/banner.css",
        "css/taikhoan.css",
        "css/trangchu.css",
        "css/home_products.css",
        "css/pagination_phantrang.css",
        "css/footer.css",
    ]
    cates = utils.load_categories()
    products = utils.load_products()
    return render_template(
        "blog/index.html",
        title="Thế giới di động",
        css_file=css_file,
        categories=cates,
        products=products,
    )


@bp.route("/login")
def login():
    return render_template("auth/login.html")


@bp.route("/register")
def register():
    return render_template("auth/register.html")


@bp.route("/cart")
def cart():
    return render_template("blog/cart.html")


@bp.route("/products_details")
def products_details():
    return render_template("blog/products_details.html")


@bp.route("/user")
def user():
    return render_template("blog/user.html")


@bp.route("/news")
def news():
    return render_template("blog/news.html")


@bp.route("/recruitment")
def recruitment():
    return render_template("blog/recruitment.html")


@bp.route("/introduce")
def introduce():
    return render_template("blog/introduce.html")
