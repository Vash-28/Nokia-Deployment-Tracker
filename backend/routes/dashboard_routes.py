from flask import Blueprint, render_template
from models.accounts import (
    get_account_stats, get_all_accounts, get_all_customers,
    create_account, create_customer
)
from models.opportunity import (
    get_all_opportunities,
    get_opportunity_pos,
    create_opportunity,
    get_accounts_for_dropdown,
    get_customer_map,
    get_divisions_for_dropdown,
    get_products_for_dropdown,
    get_opportunity_stats,
    get_customers_for_filter,
)
from models.po import (
    get_all_pos,
    get_po_stats,
    get_po_products,
    create_po,
    get_opportunities_for_dropdown,
    get_products_by_opportunity_for_po,
)
from models.product import (
    get_product_stats, get_all_products,
    get_divisions_for_dropdown, create_product
)
from models.users import (
    get_all_users,
    get_user_stats,
    get_all_divisions_for_form,
    get_all_customers_for_form,
    create_user,
    update_user,
    deactivate_user,
)

dash = Blueprint("dash", __name__)
@dash.route("/dashboard")
def dashboard():
    counts = {
        "accounts": len(get_all_accounts()),
        "customers": len(get_all_customers()),
        "opportunities": len(get_all_opportunities()),
        "po": len(get_all_pos()),
        "products": len(get_all_products()),
        "users": len(get_all_users())
    }
    return render_template("dashboard.html", counts=counts, active_page="dashboard")