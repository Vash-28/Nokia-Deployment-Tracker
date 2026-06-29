from flask import Flask
from db import get_db_connection
from routes.accounts_routes import accounts_bp
from routes.opportunities_routes import opportunities_bp
from routes.po_routes import po_bp
from routes.users_routes import users_bp
from routes.auth_routes import auth
from routes.dashboard_routes import dash
from routes.products_routes import products_bp
from routes.milestone_routes import milestone_bp
from routes.challenges_routes import challenges_bp


app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend")
app.secret_key = "nokiasecret123"

app.register_blueprint(accounts_bp)
app.register_blueprint(opportunities_bp)
app.register_blueprint(users_bp)
app.register_blueprint(po_bp)
app.register_blueprint(auth)
app.register_blueprint(dash)
app.register_blueprint(products_bp)
app.register_blueprint(milestone_bp)
app.register_blueprint(challenges_bp)

conn = get_db_connection()

if __name__ == "__main__":
    app.run(debug=True)



