
from flask import Flask, render_template, request, redirect, url_for, session
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = "ecommerce123"
#Logistic regression model
model = joblib.load("saved_models/logistic_model.pkl")
# KNN Model
knn_model = joblib.load("saved_models/knn_model.pkl")

# Product Dataset
products_df = pd.read_csv("data/products.csv")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    result = ""

    if request.method == "POST":

        age = int(request.form["age"])
        income = int(request.form["income"])
        previous = int(request.form["previous"])
        time = int(request.form["time"])

        prediction = model.predict([[age, income, previous, time]])

        if prediction[0] == 1:
            result = "✅ Customer is likely to Purchase"
        else:
            result = "❌ Customer is not likely to Purchase"

    return render_template("prediction.html", result=result)

@app.route("/login", methods=["GET","POST"])
def login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        users = pd.read_csv("data/users.csv")

        user = users[
            (users["Username"] == username) &
            (users["Password"] == password)
        ]

        if not user.empty:
            session["user"] = username
            message = "✅ Login Successful"
            return redirect(url_for("profile"))

        else:
            message = "❌ Invalid Username or Password"

    return render_template("login.html", message=message)

@app.route("/register", methods=["GET","POST"])
def register():

    message=""

    if request.method=="POST":

        username=request.form["username"]
        email=request.form["email"]
        password=request.form["password"]

        users=pd.read_csv("data/users.csv")

        users.loc[len(users)] = [username,email,password]

        users.to_csv("data/users.csv",index=False)

        message="✅ Registration Successful"

    return render_template("register.html",message=message)

@app.route("/products")
def products_page():

    products = pd.read_csv("data/products.csv")

    category = request.args.get("category")
    brand = request.args.get("brand")
    price = request.args.get("price")

    if category and category != "All":
        products = products[products["Category"] == category]

    if brand and brand != "All":
        products = products[products["Brand"] == brand]

    if price:
        products = products[products["Price"] <= int(price)]

    categories = pd.read_csv("data/products.csv")["Category"].unique()

    brands = pd.read_csv("data/products.csv")["Brand"].unique()

    return render_template(
        "products.html",
        products=products.to_dict(orient="records"),
        categories=categories,
        brands=brands
    )

@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):

    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]
    cart.append(product_id)
    session["cart"] = cart

    return redirect(url_for("cart"))

@app.route("/cart")
def cart():

    products = pd.read_csv("data/products.csv").to_dict(orient="records")

    cart_items = []
    total = 0

    if "cart" in session:

        for pid in session["cart"]:

            product = next(
                (p for p in products if int(p["ProductID"]) == pid),
                None
            )

            if product:
                cart_items.append(product)
                total += int(product["Price"])

    return render_template(
        "cart.html",
        cart_items=cart_items,
        total=total
    )


@app.route("/recommendation", methods=["GET", "POST"])
def recommendation():

    recommendations = []

    if request.method == "POST":

        price = int(request.form["price"])
        rating = float(request.form["rating"])

        distances, indices = knn_model.kneighbors([[price, rating]])

        recommendations = products_df.iloc[indices[0]].to_dict(orient="records")

    return render_template(
        "recommendation.html",
        recommendations=recommendations
    )

@app.route("/customer-analysis")
def customer_analysis():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    df = pd.read_csv("data/customer_data.csv")

    gender_count = df["Gender"].value_counts()

    plt.figure(figsize=(5,5))

    plt.pie(
        gender_count,
        labels=gender_count.index,
        autopct="%1.1f%%"
    )

    plt.title("Customer Distribution")

    chart_path = "static/images/customer_chart.png"

    plt.savefig(chart_path)

    plt.close()

    return render_template(
        "customer_analysis.html",
        chart="images/customer_chart.png"
    )


@app.route("/product-management")
def product_management():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    products = pd.read_csv("data/products.csv")

    search = request.args.get("search")
    category = request.args.get("category")

    if search:
        products = products[
            products["ProductName"].str.contains(search, case=False)
        ]

    if category and category != "All":
        products = products[
            products["Category"] == category
        ]

    categories = pd.read_csv("data/products.csv")["Category"].unique()

    return render_template(

        "product_management.html",

        products=products.to_dict(orient="records"),

        categories=categories

    )
@app.route("/add-product", methods=["GET","POST"])
def add_product():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":

        df = pd.read_csv("data/products.csv")

        new_id = len(df) + 1

        new_product = {
            "ProductID": new_id,
            "ProductName": request.form["name"],
            "Category": request.form["category"],
            "Brand": request.form["brand"],
            "Price": int(request.form["price"]),
            "Rating": float(request.form["rating"]),
            "Stock": int(request.form["stock"]),
            "images": request.form["image"]
        }

        df.loc[len(df)] = new_product

        df.to_csv("data/products.csv", index=False)

        return redirect(url_for("product_management"))

    return render_template("add_product.html")

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    message = ""

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        admin = pd.read_csv("data/admin.csv")

        user = admin[
            (admin["Username"] == username) &
            (admin["Password"] == password)
        ]

        if not user.empty:

            session["admin"] = username

            return redirect(url_for("admin_dashboard"))

        else:

            message = "❌ Invalid Admin Username or Password"

    return render_template(
        "admin_login.html",
        message=message
    )



@app.route("/admin/dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    products = pd.read_csv("data/products.csv")
    users = pd.read_csv("data/users.csv")
    orders = pd.read_csv("data/orders.csv")

    total_products = len(products)
    total_users = len(users)
    total_orders = len(orders)
    total_revenue = orders["Price"].sum()

    average_rating = round(
        products["Rating"].mean(),
        1
    )

    highest_product = products.loc[
        products["Rating"].idxmax(),
        "ProductName"
    ]

    popular_category = products["Category"].mode()[0]

    return render_template(
        "admin_dashboard.html",
        products=total_products,
        users=total_users,
        orders=total_orders,
        revenue=total_revenue,
        average_rating=average_rating,
        highest_product=highest_product,
        popular_category=popular_category
    )

@app.route("/product/<int:product_id>", methods=["GET", "POST"])
def product_details(product_id):

    # Read products
    products = pd.read_csv("data/products.csv")

    # Find selected product
    product = products[products["ProductID"] == product_id]

    if product.empty:
        return "Product Not Found"

    product = product.iloc[0].to_dict()

    # Read reviews
    reviews = pd.read_csv("data/reviews.csv")

    # Add new review
    if request.method == "POST":

        username = request.form["username"]
        rating = int(request.form["rating"])
        review = request.form["review"]

        reviews.loc[len(reviews)] = [
            product_id,
            username,
            rating,
            review
        ]

        reviews.to_csv("data/reviews.csv", index=False)

        return redirect(url_for(
            "product_details",
            product_id=product_id
        ))

    # Get reviews for this product
    product_reviews = reviews[
        reviews["ProductID"] == product_id
    ]

    # Calculate average rating
    if len(product_reviews) > 0:
        average_rating = round(
            product_reviews["Rating"].mean(),
            1
        )
    else:
        average_rating = 0

    return render_template(
        "product_details.html",
        product=product,
        reviews=product_reviews.to_dict(orient="records"),
        average_rating=average_rating
    )

@app.route("/wishlist/<int:product_id>")
def wishlist(product_id):

    if "wishlist" not in session:
        session["wishlist"] = []

    wishlist = session["wishlist"]

    if product_id not in wishlist:
        wishlist.append(product_id)

    session["wishlist"] = wishlist

    return redirect(url_for("wishlist_page"))

@app.route("/wishlist")
def wishlist_page():

    products = pd.read_csv("data/products.csv").to_dict(orient="records")

    wishlist_items = []

    if "wishlist" in session:

        for pid in session["wishlist"]:

            product = next(
                (p for p in products if int(p["ProductID"]) == pid),
                None
            )

            if product:
                wishlist_items.append(product)

    return render_template(
        "wishlist.html",
        wishlist_items=wishlist_items
    )

from datetime import datetime

@app.route("/invoice")
def invoice():

    orders = pd.read_csv("data/orders.csv")

    if orders.empty:

        return "No Orders Found"

    # Get the latest Order ID
    latest_order = orders["OrderID"].max()

    # Get all products belonging to the latest order
    invoice_items = orders[
        orders["OrderID"] == latest_order
    ]

    total = invoice_items["Price"].sum()

    return render_template(

        "invoice.html",

        cart_items=invoice_items.to_dict(orient="records"),

        total=total,

        invoice=latest_order,

        date=datetime.now().strftime("%d-%m-%Y")

    )
from datetime import datetime

@app.route("/place-order", methods=["POST"])
def place_order():

    products = pd.read_csv("data/products.csv").to_dict(orient="records")
    orders = pd.read_csv("data/orders.csv")

    if "cart" in session:

        order_id = len(orders) + 1

        for pid in session["cart"]:

            product = next(
                (p for p in products if int(p["ProductID"]) == pid),
                None
            )

            if product:

                orders.loc[len(orders)] = [
    order_id,
    session["user"],
    product["ProductID"],
    product["ProductName"],
    product["Price"],
    datetime.now().strftime("%d-%m-%Y"),
    "Pending"
]                

                order_id += 1

        orders.to_csv("data/orders.csv", index=False)

        session["cart"] = []

    return render_template(
    "checkout_success.html",
    success=True
    
)
@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/orders")
def orders():

    if "user" not in session:
        return redirect(url_for("login"))

    orders = pd.read_csv("data/orders.csv")

    user_orders = orders[
        orders["Username"] == session["user"]
    ]

    return render_template(
        "orders.html",
        orders=user_orders.to_dict(orient="records")
    )

@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect(url_for("login"))

    users = pd.read_csv("data/users.csv")

    user = users[
        users["Username"] == session["user"]
    ]

    if user.empty:
        return redirect(url_for("login"))

    user = user.iloc[0]

    return render_template(
        "profile.html",
        user=user
    )
@app.route("/admin/logout")
def admin_logout():

    session.pop("admin", None)

    return redirect(url_for("admin_login"))

@app.route("/edit-product/<int:id>", methods=["GET", "POST"])
def edit_product(id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    df = pd.read_csv("data/products.csv")

    index = df[df["ProductID"] == id].index

    if len(index) == 0:
        return "Product Not Found"

    index = index[0]

    if request.method == "POST":

        df.loc[index, "ProductName"] = request.form["name"]
        df.loc[index, "Category"] = request.form["category"]
        df.loc[index, "Brand"] = request.form["brand"]
        df.loc[index, "Price"] = int(request.form["price"])
        df.loc[index, "Rating"] = float(request.form["rating"])
        df.loc[index, "Stock"] = int(request.form["stock"])
        df.loc[index, "Image"] = request.form["image"]

        df.to_csv("data/products.csv", index=False)

        return redirect(url_for("product_management"))

    product = df.loc[index]

    return render_template(
        "edit_product.html",
        product=product
    )

@app.route("/delete-product/<int:id>")
def delete_product(id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    df = pd.read_csv("data/products.csv")

    df = df[df["ProductID"] != id]

    # Reset ProductID
    df = df.reset_index(drop=True)
    df["ProductID"] = range(1, len(df) + 1)

    df.to_csv("data/products.csv", index=False)

    return redirect(url_for("product_management"))

@app.route("/admin/orders")
def admin_orders():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    orders = pd.read_csv("data/orders.csv")

    return render_template(
        "admin_orders.html",
        orders=orders.to_dict(orient="records")
    )

@app.route("/update-order-status/<int:order_id>", methods=["POST"])
def update_order_status(order_id):

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    status = request.form["status"]

    orders = pd.read_csv("data/orders.csv")

    orders.loc[
        orders["OrderID"] == order_id,
        "Status"
    ] = status

    orders.to_csv("data/orders.csv", index=False)

    return redirect(url_for("admin_orders"))

@app.route("/admin/users")
def admin_users():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    users = pd.read_csv("data/users.csv")

    return render_template(
        "admin_users.html",
        users=users.to_dict(orient="records")
    )

@app.route("/admin/sales-analytics")
def sales_analytics():

    if "admin" not in session:
        return redirect(url_for("admin_login"))

    orders = pd.read_csv("data/orders.csv")
    products = pd.read_csv("data/products.csv")

    total_orders = len(orders)
    total_revenue = orders["Price"].sum()
    average_order = round(orders["Price"].mean(), 2)

    best_product = orders["ProductName"].mode()[0]

    # Revenue Chart
    plt.figure(figsize=(8,5))

    revenue = orders.groupby("ProductName")["Price"].sum()

    revenue.plot(kind="bar")

    plt.title("Revenue by Product")
    plt.ylabel("Revenue (₹)")
    plt.xticks(rotation=30)

    plt.tight_layout()

    chart_path = "static/images/sales_chart.png"

    plt.savefig(chart_path)

    plt.close()

    return render_template(

        "sales_analytics.html",

        total_orders=total_orders,

        total_revenue=total_revenue,

        average_order=average_order,

        best_product=best_product,

        chart="images/sales_chart.png"

    )
@app.route("/payment")
def payment():

    if "cart" not in session or len(session["cart"]) == 0:
        return redirect(url_for("cart"))

    return render_template("payment.html")

@app.route("/chatbot", methods=["GET","POST"])
def chatbot():

    reply = ""

    if request.method == "POST":

        message = request.form["message"].lower()

        if "electronics" in message:

            reply = "Smart Watch, Headphones, Bluetooth Speaker"

        elif "accessories" in message:

            reply = "Laptop Backpack"

        elif "bag" in message:

            reply = "Laptop Backpack is available."

        elif "watch" in message:

            reply = "Smart Watch - ₹4999"

        elif "hello" in message or "hi" in message:

            reply = "Hello 👋 Welcome to Velora."

        else:

            reply = "Sorry, I couldn't understand."

    return render_template(
        "chatbot.html",
        reply=reply
    )

@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect(url_for("home"))

@app.route("/buy-now/<int:product_id>")
def buy_now(product_id):

    session["cart"] = [product_id]

    return redirect(url_for("payment"))

@app.route("/remove-from-cart/<int:product_id>")
def remove_from_cart(product_id):

    if "cart" in session:

        cart = session["cart"]

        if product_id in cart:

            cart.remove(product_id)

        session["cart"] = cart

    return redirect(url_for("cart"))

if __name__ == "__main__":
    app.run(debug=True)