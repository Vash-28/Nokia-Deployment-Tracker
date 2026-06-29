from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.users import (
    get_all_users,
    get_user_stats,
    get_all_divisions_for_form,
    get_all_customers_for_form,
    create_user,
    update_user,
    deactivate_user,
)

users_bp = Blueprint('users', __name__)


# ── List ──────────────────────────────────────────────────────────────────────

@users_bp.route('/users')
def users():
    all_users     = get_all_users()
    stats         = get_user_stats()
    all_divisions = get_all_divisions_for_form()
    all_customers = get_all_customers_for_form()
    return render_template(
        'users/users.html',
        users=all_users,
        stats=stats,
        all_divisions=all_divisions,
        all_customers=all_customers,
        active_page='users'
    )


# ── New user ──────────────────────────────────────────────────────────────────

@users_bp.route('/users/new', methods=['GET', 'POST'])
def user_new():
    if request.method == 'GET':
        return render_template(
            'users/user_new.html',
            divisions=get_all_divisions_for_form(),
            customers=get_all_customers_for_form(),
            active_page='users'
        )

    form         = request.form
    role_val     = form.get('roleVal', '0')
    is_superadmin = 1 if role_val == 'super' else 0
    user_role     = 1 if role_val == '1' else 0

    user_data = {
        'userName':     form.get('userName', '').strip(),
        'emailAddress': form.get('emailAddress', '').strip(),
        'mobile':       form.get('mobile', '').strip() or None,
        'userPassword': form.get('userPassword', ''),
        'isSuperAdmin': is_superadmin,
        'userRole':     user_role,
        'isActive':     int(form.get('isActive', 1)),
    }
    division_ids = [int(x) for x in form.getlist('divisionIDs')]
    customer_ids = [int(x) for x in form.getlist('customerIDs')]

    if not user_data['userName'] or not user_data['emailAddress']:
        flash('Name and email are required.', 'error')
        return redirect(url_for('users.user_new'))

    try:
        create_user(user_data, division_ids, customer_ids)
        flash('User created successfully.', 'success')
        return redirect(url_for('users.users'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('users.user_new'))


# ── Inline edit (AJAX) ────────────────────────────────────────────────────────

@users_bp.route('/users/<int:user_id>/edit', methods=['POST'])
def user_edit(user_id):
    data = request.get_json()
    try:
        role_val      = data.get('roleVal', '0')
        is_superadmin = 1 if role_val == 'super' else 0
        user_role     = 1 if role_val == '1' else 0

        update_data = {
            'userName':     data.get('userName', '').strip(),
            'emailAddress': data.get('emailAddress', '').strip(),
            'mobile':       data.get('mobile', '').strip() or None,
            'isSuperAdmin': is_superadmin,
            'userRole':     user_role,
            'isActive':     int(data.get('isActive', 1)),
            'password':     data.get('password'),   # None = don't change
        }
        division_ids = data.get('divisionIDs', [])
        customer_ids = data.get('customerIDs', [])

        update_user(user_id, update_data, division_ids, customer_ids)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ── Delete / deactivate (AJAX) ────────────────────────────────────────────────

@users_bp.route('/users/<int:user_id>/delete', methods=['POST'])
def user_delete(user_id):
    try:
        deactivate_user(user_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500