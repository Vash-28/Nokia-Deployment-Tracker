from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import date
from models.po import (
    get_all_pos,
    get_po_stats,
    get_po_products,
    create_po,
    get_opportunities_for_dropdown,
    get_products_by_opportunity_for_po,
)
from models.opportunity import (
    get_accounts_for_dropdown,
    get_customers_for_filter,
)
from models.accounts import (
    get_all_accounts_for_dropdown,
)
po_bp = Blueprint('po', __name__)


# ── List ──────────────────────────────────────────────────────────────────────

@po_bp.route('/po')
def po_list():
    pos          = get_all_pos()
    stats        = get_po_stats()
    accounts     = get_all_accounts_for_dropdown()
    customers    = get_customers_for_filter()
    opportunities = get_opportunities_for_dropdown()
    return render_template(
        'po/po.html',
        pos=pos,
        stats=stats,
        accounts=accounts,
        customers=customers,
        opportunities=opportunities,
        now=date.today(),
        active_page='po'
    )


# ── Product sub-rows (AJAX from PO list expand) ───────────────────────────────

@po_bp.route('/po/<int:po_id>/products')
def po_products(po_id):
    """
    Returns JSON list of products for the expand-row in the PO table.
    Each product: { productID, productName, opp_qty, po_qty, deployed }
    """
    products = get_po_products(po_id)
    return jsonify(products)


# ── Create ────────────────────────────────────────────────────────────────────

@po_bp.route('/po/create', methods=['GET', 'POST'])
def po_create():
    if request.method == 'GET':
        accounts      = get_accounts_for_dropdown()
        opportunities = get_opportunities_for_dropdown()
        return render_template(
            'po/po_create.html',
            accounts=accounts,
            opportunities=opportunities,
            active_page='po'
        )

    # ── POST ──
    form = request.form

    po_data = {
        'pOName':        form.get('pOName', '').strip(),
        'opportunityID': int(form.get('opportunityID')),
        'startDate':     form.get('startDate'),
        'endDate':       form.get('endDate') or None,
        'totalValue':    float(form.get('totalValue', 0)),
        'poRemark':      form.get('poRemark', '').strip() or None,
        'createdBy':     session.get('user_id'),
    }

    product_ids    = form.getlist('product_id[]')
    product_qtys   = form.getlist('product_qty[]')
    product_rates  = form.getlist('product_rate[]')
    product_totals = form.getlist('product_total[]')

    details = []
    for pid, qty, rate, total in zip(product_ids, product_qtys, product_rates, product_totals):
        if pid:
            details.append({
                'productID':       int(pid),
                'productQuantity': float(qty),
                'productRate':     float(rate),
                'productTotal':    float(total),
            })

    if not details:
        flash('Please add at least one product.', 'error')
        return redirect(url_for('po.po_create'))

    try:
        create_po(po_data, details)
        flash('Purchase Order created successfully.', 'success')
        return redirect(url_for('po.po_list'))
    except Exception as e:
        flash(f'Error creating PO: {str(e)}', 'error')
        return redirect(url_for('po.po_create'))


# ── Products for PO create form (AJAX) ───────────────────────────────────────

@po_bp.route('/opportunities/<int:opp_id>/products-for-po')
def products_for_po(opp_id):
    """
    Returns products from Opportunity_Details for a given opportunity.
    Used by the PO create form when an opportunity is selected.
    Each product: { productID, productName, productUOM, opp_qty }
    """
    products = get_products_by_opportunity_for_po(opp_id)
    return jsonify(products)


# ── Export ────────────────────────────────────────────────────────────────────

@po_bp.route('/po/export')
def po_export():
    flash('Export coming soon.', 'success')
    return redirect(url_for('po.po_list'))