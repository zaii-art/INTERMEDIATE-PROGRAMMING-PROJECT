from flask import Flask, request, render_template, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# =========================
# DATA STORAGE (MOCK)
# =========================

users = {
    "ADMIN": ["KING", "admin"],
    "STAFF": ["SLAVE", "staff"]
}

discounts = {}
discount_id_counter = 1

products = {
    "p1": {"id": "p1", "name": "T-Shirt", "price": 200, "category": "Clothing"},
    "p2": {"id": "p2", "name": "Shoes", "price": 500, "category": "Footwear"},
    "p3": {"id": "p3", "name": "Cap", "price": 300, "category": "Accessories"},
    "p4": {"id": "p4", "name": "Jacket", "price": 500, "category": "Clothing"},
    "p5": {"id": "p5", "name": "Knife", "price": 700, "category": "Kitchen"},
    "p6": {"id": "p6", "name": "Short", "price": 150, "category": "Clothing"},
    "p7":{"id": "p7", "name": "Baggy Pants", "price": 250, "category": "Clothing"}
}

categories = ["Clothing", "Footwear", "Accessories", "Kitchen"]

# =========================
# HELPER FUNCTIONS
# =========================

def format_datetime(dt_string):
    """Converts ISO format to a user-friendly string."""
    try:
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M")
        return dt.strftime("%B %d, %Y - %I:%M %p")
    except:
        return dt_string

def calculate_price(product_price, discount_type, value):
    """Calculates final price based on discount type."""
    if discount_type == "Percentage":
        final = product_price - (product_price * value / 100)
    elif discount_type == "Fixed":
        final = product_price - value
    else:
        final = product_price
    return max(final, 0)

# =========================
# ROUTES
# =========================

@app.route("/")
def intro():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users.get(username)
        if user and password == user[0]:
            role = user[1]
            return redirect(url_for("admin" if role == "admin" else "staff"))
        else:
            message = "Invalid username or password"
    return render_template("login.html", message=message)

@app.route("/register", methods=["GET", "POST"])
def register():
    message, message_type = "", ""
    if request.method == "POST":
        username, password = request.form["username"], request.form["password"]
        if username in users:
            message, message_type = "Username already exists.", "error"
        else:
            users[username] = [password, "staff"]
            message, message_type = "Account successfully created.", "success"
    return render_template("register.html", message=message, message_type=message_type)

@app.route("/admin")
def admin(): 
    return render_template("admin.html")

@app.route("/staff")
def staff(): 
    return render_template("staff.html")

# =========================
# DISCOUNTS MANAGEMENT
# =========================

@app.route("/discounts")
def discounts_page():
    now = datetime.now()
    for discount_id, d in discounts.items():
        start_time = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(d["end"], "%Y-%m-%dT%H:%M")

        if now < start_time: d["status"] = "Upcoming"
        elif now > end_time: d["status"] = "Expired"
        else: d["status"] = "Active"

        d["start_readable"] = format_datetime(d["start"])
        d["end_readable"] = format_datetime(d["end"])

    return render_template("discounts.html", discounts=discounts, products=products, categories=categories)

@app.route("/create_discount", methods=["POST"])
def create_discount():
    global discount_id_counter
    try:
        name = request.form["name"]
        discount_type = request.form["type"]
        value = float(request.form["value"])
        start, end = request.form["start"], request.form["end"]
        apply_type = request.form["apply_type"]
        product_id = request.form.get("product_id")
        category = request.form.get("category")

        # Backend Validations (Security Layer)
        if value <= 0:
            flash("Discount value must be greater than 0.", "error")
            return redirect(url_for("discounts_page"))
        
        if discount_type == "Percentage" and value > 100:
            flash("Percentage discount cannot exceed 100%.", "error")
            return redirect(url_for("discounts_page"))

        if end <= start:
            flash("End date must be later than Start date.", "error")
            return redirect(url_for("discounts_page"))

        discount_id = f"disc_{discount_id_counter:03d}"
        discounts[discount_id] = {
            "name": name, "type": discount_type, "value": value,
            "start": start, "end": end, "apply_type": apply_type,
            "product_id": product_id, "category": category
        }
        discount_id_counter += 1
        flash("Discount created successfully!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("discounts_page"))

@app.route("/update_discount/<discount_id>", methods=["POST"])
def update_discount(discount_id):
    if discount_id not in discounts:
        flash("Discount not found.", "error")
        return redirect(url_for("discounts_page"))

    d = discounts[discount_id]
    now = datetime.now()
    start_time = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M")
    end_time = datetime.strptime(d["end"], "%Y-%m-%dT%H:%M")

    if now > end_time:
        flash("Expired discounts cannot be edited.", "error")
        return redirect(url_for("discounts_page"))

    # Update Name
    d["name"] = request.form["name"]

    # Only allow editing core details if the discount isn't Active yet
    if now < start_time:
        try:
            val = float(request.form["value"])
            dtype = request.form["type"]
            
            if dtype == "Percentage" and val > 100:
                flash("Percentage cannot exceed 100%.", "error")
                return redirect(url_for("discounts_page"))

            d["type"] = dtype
            d["value"] = val
            d["start"] = request.form["start"]
            d["end"] = request.form["end"]
            d["apply_type"] = request.form["apply_type"]
            d["product_id"] = request.form.get("product_id")
            d["category"] = request.form.get("category")
            
            flash("Discount updated successfully!", "success")
        except:
            flash("Invalid input data.", "error")
    else:
        flash("Active discount: only the name was updated.", "success")

    return redirect(url_for("discounts_page"))

@app.route("/delete_discount/<discount_id>")
def delete_discount(discount_id):
    if discount_id in discounts:
        d = discounts[discount_id]
        if datetime.now() > datetime.strptime(d["end"], "%Y-%m-%dT%H:%M"):
            flash("Expired discounts cannot be deleted.", "error")
        else:
            del discounts[discount_id]
            flash("Discount deleted.", "success")
    return redirect(url_for("discounts_page"))

# =========================
# PRODUCT VIEWS (ADMIN & STAFF)
# =========================

@app.route("/products")
def product_page():
    now = datetime.now()
    product_list = []
    for pid, p in products.items():
        original_price = p["price"]
        final_price, active_discount = original_price, None
        for d in discounts.values():
            start = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M")
            end = datetime.strptime(d["end"], "%Y-%m-%dT%H:%M")
            if start <= now <= end:
                if (d["apply_type"] == "product" and d["product_id"] == pid) or \
                   (d["apply_type"] == "category" and p["category"] == d["category"]):
                    final_price = calculate_price(original_price, d["type"], d["value"])
                    active_discount = d
        product_list.append({
            "name": p["name"], "original": original_price, "category": p["category"],
            "final": round(final_price, 2), "saved": round(original_price - final_price, 2), "discount": active_discount
        })
    return render_template("products.html", products=product_list, categories=categories)

@app.route("/staff_products")
def staff_product_page():
    now = datetime.now()
    product_list = []
    for pid, p in products.items():
        original_price = p["price"]
        final_price, active_discount = original_price, None
        for d in discounts.values():
            start = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M")
            end = datetime.strptime(d["end"], "%Y-%m-%dT%H:%M")
            if start <= now <= end:
                if (d["apply_type"] == "product" and d["product_id"] == pid) or \
                   (d["apply_type"] == "category" and p["category"] == d["category"]):
                    final_price = calculate_price(original_price, d["type"], d["value"])
                    active_discount = d
        product_list.append({
            "name": p["name"], "original": original_price, "category": p["category"],
            "final": round(final_price, 2), "saved": round(original_price - final_price, 2), "discount": active_discount
        })
    return render_template("staff_products_view.html", products=product_list, categories=categories)

@app.route("/staff_discounts")
def staff_discounts_page():
    now = datetime.now()
    for d in discounts.values():
        start_time = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(d["end"], "%Y-%m-%dT%H:%M")
        if now < start_time: d["status"] = "Upcoming"
        elif now > end_time: d["status"] = "Expired"
        else: d["status"] = "Active"
        d["start_readable"] = format_datetime(d["start"])
    return render_template("staff_discounts_view.html", discounts=discounts, products=products)

# --- Admin Reports Route ---
@app.route("/daily_reports")
def daily_reports_page():
    data = get_discount_stats()
    return render_template("reports.html", **data)

# --- Staff Reports Route ---
@app.route("/staff_reports")
def staff_reports_page():
    # Calling the exact same data as Admin
    data = get_discount_stats()
    return render_template("staff_reports.html", **data)

def get_discount_stats():
    """Shared logic to calculate discount statistics for both Admin and Staff."""
    now = datetime.now()
    stats = {
        "total": len(discounts),
        "active": 0,
        "upcoming": 0,
        "expired": 0,
        "percentage_count": 0,
        "fixed_count": 0,
        "product_target": 0,
        "category_target": 0,
        "total_perc_val": 0,
        "total_fixed_val": 0
    }

    for d in discounts.values():
        start = datetime.strptime(d["start"], "%Y-%m-%dT%H:%M")
        end = datetime.strptime(d["end"], "%Y-%m-%dT%H:%M")

        # Status Logic
        if now < start: stats["upcoming"] += 1
        elif now > end: stats["expired"] += 1
        else: stats["active"] += 1

        # Type Logic
        if d["type"] == "Percentage":
            stats["percentage_count"] += 1
            stats["total_perc_val"] += d["value"]
        else:
            stats["fixed_count"] += 1
            stats["total_fixed_val"] += d["value"]

        # Target Logic
        if d["apply_type"] == "product": stats["product_target"] += 1
        else: stats["category_target"] += 1

    # Calculation for UI display
    avg_perc = round(stats["total_perc_val"] / stats["percentage_count"], 1) if stats["percentage_count"] > 0 else 0
    avg_fixed = round(stats["total_fixed_val"] / stats["fixed_count"], 1) if stats["fixed_count"] > 0 else 0
    
    total_targets = stats["product_target"] + stats["category_target"]
    prod_p = round((stats["product_target"] / total_targets) * 100) if total_targets > 0 else 0
    cat_p = 100 - prod_p if total_targets > 0 else 0

    return {
        "stats": stats, 
        "avg_perc": avg_perc, 
        "avg_fixed": avg_fixed, 
        "prod_p": prod_p, 
        "cat_p": cat_p
    }


if __name__ == "__main__":
    app.run(debug=True)
