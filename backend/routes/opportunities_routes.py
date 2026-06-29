from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import date
from models.opportunity import (
    get_all_opportunities,
    get_opportunity_pos,
    create_opportunity,
    get_customer_map,
    get_divisions_for_dropdown,
    get_products_for_dropdown,
    get_opportunity_stats,
    get_customers_for_filter,
)
from models.accounts import (
    get_all_accounts_for_dropdown,
)

opportunities_bp = Blueprint('opportunities', __name__)


# ── List ──────────────────────────────────────────────────────────────────────

@opportunities_bp.route('/opportunities')
def opportunities():
    opportunities = get_all_opportunities()
    stats         = get_opportunity_stats()
    accounts      = get_all_accounts_for_dropdown()
    customers     = get_customers_for_filter()
    return render_template(
        'opportunities/opportunities.html',
        opportunities=opportunities,
        stats=stats,
        accounts=accounts,
        customers=customers,
        now=date.today(),
        active_page='opportunities'
    )


# ── PO sub-rows (AJAX) ────────────────────────────────────────────────────────

@opportunities_bp.route('/opportunities/<int:opp_id>/pos')
def opportunity_pos(opp_id):
    """
    Returns JSON list of POs for the expand-row in the opportunities table.
    Each PO has: poID, pOName, products[], opp_qty, po_qty, deployed
    """
    pos = get_opportunity_pos(opp_id)
    return jsonify(pos)


# ── Create ────────────────────────────────────────────────────────────────────

@opportunities_bp.route('/opportunities/create', methods=['GET', 'POST'])
def opportunity_create():
    if request.method == 'GET':
        accounts     = get_all_accounts_for_dropdown()
        customer_map = get_customer_map()          # {accountID: [{customerID, customerName}]}
        divisions    = get_divisions_for_dropdown()
        products     = get_products_for_dropdown()
        return render_template(
            'opportunities/opportunity_create.html',
            accounts=accounts,
            customer_map=customer_map,
            divisions=divisions,
            products=products,
            active_page='opportunities'
        )

    # ── POST: parse and insert ──
    form = request.form

    # Header fields
    opp_data = {
        'opportunityName':   form.get('opportunityName', '').strip(),
        'opportunityNumber': form.get('opportunityNumber', '').strip() or None,
        'customerID':        int(form.get('customerID')),
        'divisionID':        int(form.get('divisionID')) if form.get('divisionID') else None,
        'startDate':         form.get('startDate'),
        'endDate':           form.get('endDate') or None,
        'totalValue':        float(form.get('totalValue', 0)),
        'createdBy':         session.get('user_id'),
    }

    # Product rows (parallel arrays from form)
    product_ids    = form.getlist('product_id[]')
    product_qtys   = form.getlist('product_qty[]')
    product_rates  = form.getlist('product_rate[]')
    product_totals = form.getlist('product_total[]')
    product_remarks = form.getlist('product_remark[]')  # optional

    details = []
    for pid, qty, rate, total in zip(product_ids, product_qtys, product_rates, product_totals):
        if pid:
            details.append({
                'productID':      int(pid),
                'productQuantity': float(qty),
                'productRate':    float(rate),
                'productTotal':   float(total),
            })

    if not details:
        flash('Please add at least one product.', 'error')
        return redirect(url_for('opportunities.opportunity_create'))

    try:
        create_opportunity(opp_data, details)
        flash('Opportunity created successfully.', 'success')
        return redirect(url_for('opportunities.opportunities'))
    except Exception as e:
        flash(f'Error creating opportunity: {str(e)}', 'error')
        return redirect(url_for('opportunities.opportunity_create'))


# ── Export ────────────────────────────────────────────────────────────────────

@opportunities_bp.route('/opportunities/export')
def opportunity_export():
    """
    Streams a CSV of all opportunities + details.
    Implement using csv module or openpyxl in the model layer.
    """
    # TODO: implement export_opportunities() in model
    flash('Export coming soon.', 'success')
    return redirect(url_for('opportunities.opportunities'))