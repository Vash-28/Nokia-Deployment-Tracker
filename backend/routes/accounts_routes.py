from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.accounts import (
    get_account_stats, get_all_accounts,
    get_all_accounts_for_dropdown, create_account, create_customer,
    get_customers_for_account
)
from models.opportunity import (get_all_opportunities)

accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route('/accounts')
def accounts():
    return render_template('accounts/accounts.html',
                           active_page='accounts',
                           stats=get_account_stats(),
                           accounts=get_all_accounts(),
                           total_opportunities=len(get_all_opportunities()))


@accounts_bp.route('/accounts/<int:account_id>/customers')
def account_customers(account_id):
    try:
        customers = get_customers_for_account(account_id)
        return jsonify({'customers': customers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@accounts_bp.route('/accounts/new', methods=['GET', 'POST'])
def account_new():
    if request.method == 'POST':
        data = {
            'accountName':     request.form.get('accountName', '').strip(),
            'account_details': request.form.get('account_details', '').strip(),
        }
        if not data['accountName']:
            flash('Account name is required.', 'error')
            return render_template('accounts/accounts_new.html', active_page='accounts')
        try:
            create_account(data)
            flash('Account created successfully.', 'success')
            return redirect(url_for('accounts.accounts'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('accounts/accounts_new.html', active_page='accounts')


@accounts_bp.route('/customers/new', methods=['GET', 'POST'])
def customer_new():
    accs = get_all_accounts_for_dropdown()
    if request.method == 'POST':
        data = {
            'accountID':       request.form.get('accountID'),
            'customerName':    request.form.get('customerName', '').strip(),
            'customerDetails': request.form.get('customerDetails', '').strip(),
        }
        if not data['accountID'] or not data['customerName']:
            flash('Account and customer name are required.', 'error')
            return render_template('accounts/customer_new.html', active_page='accounts', accounts=accs)
        try:
            create_customer(data)
            flash('Customer created successfully.', 'success')
            return redirect(url_for('accounts.accounts'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('accounts/customers_new.html', active_page='accounts', accounts=accs)