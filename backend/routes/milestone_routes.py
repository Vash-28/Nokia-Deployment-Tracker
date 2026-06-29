from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime
from models.milestone import (
    get_pos_for_opportunity,
    get_products_for_po_tracking,
    check_tracking_exists,
    create_milestone_plans,
    get_tracking_context,
    get_tracking_months,
    get_milestone_tracking_data,
    save_actuals,
)
from models.opportunity import (
    get_accounts_for_dropdown,
    get_opportunities_for_dropdown as get_opps_ms,
)

milestone_bp = Blueprint('milestone', __name__)


# ── Milestone init page ───────────────────────────────────────────────────────

@milestone_bp.route('/milestone')
def milestone_init():
    accounts      = get_accounts_for_dropdown()
    opportunities = get_opps_ms()
    return render_template(
        'milestones/milestone_init.html',
        accounts=accounts,
        opportunities=opportunities,
        active_page='milestone'
    )


# ── AJAX: POs for a given opportunity (used by milestone init cascade) ────────

@milestone_bp.route('/milestone/pos-for-opp/<int:opp_id>')
def pos_for_opp(opp_id):
    try:
        pos = get_pos_for_opportunity(opp_id)
        return jsonify(pos)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ── AJAX: products for a PO (milestone init cascade step 3) ──────────────────

@milestone_bp.route('/milestone/products-for-po/<int:po_id>')
def products_for_po_milestone(po_id):
    """
    Returns products in a PO, plus a flag if tracking already exists
    for that specific po+product combination.
    Each item: { productID, productName, po_qty, already_tracked }
    """
    products = get_products_for_po_tracking(po_id)
    return jsonify(products)


# ── POST: create milestone plans and redirect to tracking ─────────────────────

@milestone_bp.route('/milestone/init', methods=['POST'])
def milestone_create():
    opp_id     = int(request.form.get('opportunityID'))
    po_id      = int(request.form.get('poID'))
    product_id = int(request.form.get('productID'))
    user_id    = session.get('user_id')

    # If tracking already exists, skip creation and go straight to tracking
    if check_tracking_exists(po_id, product_id):
        flash('Tracking already exists — redirected to existing tracking.', 'success')
        return redirect(url_for('milestone.po_tracking', po_id=po_id, product_id=product_id))

    try:
        create_milestone_plans(opp_id, po_id, product_id, user_id)
        flash('Milestone tracking created successfully.', 'success')
    except Exception as e:
        flash(f'Error creating milestone plans: {str(e)}', 'error')
        return redirect(url_for('milestone.milestone_init'))

    return redirect(url_for('milestone.po_tracking', po_id=po_id, product_id=product_id))


# ── Tracking page ─────────────────────────────────────────────────────────────

@milestone_bp.route('/po/tracking')
def po_tracking():
    po_id      = request.args.get('po_id', type=int)
    product_id = request.args.get('product_id', type=int)
    month      = request.args.get('month')   # format: "2024-01"

    if not po_id or not product_id:
        flash('Invalid tracking request.', 'error')
        return redirect(url_for('milestone.milestone_init'))

    # Context (account, customer, opp, po, product names + po_qty)
    context = get_tracking_context(po_id, product_id)
    if not context:
        flash('No tracking found for this PO + Product. Please initialise first.', 'error')
        return redirect(url_for('milestone.milestone_init'))

    # All months from PO start→end with has_data flag
    months = get_tracking_months(po_id, product_id)

    # Default to first month if none supplied or supplied month out of range
    valid_values = [m['value'] for m in months]
    if not month or month not in valid_values:
        month = valid_values[0] if valid_values else None

    if not month:
        flash('This PO has no valid date range for tracking.', 'error')
        return redirect(url_for('milestone.milestone_init'))

    # Current quarter label (e.g. "Q1-2024") and milestone data for that month
    paired_milestones, current_quarter = get_milestone_tracking_data(
    po_id, product_id, month
    )

    selected_month_label = datetime.strptime(month + "-01", "%Y-%m-%d").strftime("%B %Y")

    return render_template(
        'milestones/po_tracking.html',
        context=context,
        months=months,
        selected_month=month,
        selected_month_label=selected_month_label,
        current_quarter=current_quarter,
        paired_milestones=paired_milestones,   # ← changed
        po_id=po_id,
        product_id=product_id,
        active_page='po'
    )


# ── AJAX: save actuals ────────────────────────────────────────────────────────

@milestone_bp.route('/po/tracking/save', methods=['POST'])
def tracking_save():
    data       = request.get_json()
    po_id      = data.get('po_id')
    product_id = data.get('product_id')
    month      = data.get('month')
    records    = data.get('records', [])
    user_id    = session.get('user_id')

    # Filter out records with no planDetailsID
    records = [r for r in records if r.get('planDetailsID')]

    try:
        save_actuals(po_id, product_id, month, records, user_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500