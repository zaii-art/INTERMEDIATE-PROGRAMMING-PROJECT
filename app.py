from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

users = {
            "admin" : ["123", "admin"],
            "staff" : ["123", "staff"]
}

@app.route("/")
def intro():
	return render_template("intro.html")

@app.route("/login", methods = ["GET", "POST"])
def login():
	message = ""
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		remember = request.form.get("remember")
				
		user = users.get(username)
		if user and password == user[0]:
			
			role = user[1]
			if role == "admin":
				pass
			elif role == "staff":
				pass
			else:
				return "Invalid login"			
		else:
			message = "Invalid username or password"	
	return render_template("login.html", message=message)

@app.route("/register", methods=["GET", "POST"])
def register():
	message=""
	message_type=""
	
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]

		if username in users:
			message = "Username already exist. Please create another one"
			message_type="error"
		else:
			users[username] = [password, "staff"]
			message = "Account successfully created. You can now login."
			message_type ="success"
	
	return render_template("register.html", message=message, message_type=message_type)

if __name__ == "__main__":
	app.run(debug=True)