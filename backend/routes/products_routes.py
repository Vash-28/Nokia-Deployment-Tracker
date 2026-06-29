from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.product import (
    get_product_stats, get_all_products,
    get_divisions_for_dropdown, create_product
)

products_bp = Blueprint('products', __name__)


@products_bp.route('/products')
def products():
    return render_template('products/products.html',
                           active_page='products',
                           stats=get_product_stats(),
                           products=get_all_products(),
                           divisions=get_divisions_for_dropdown())


@products_bp.route('/products/new', methods=['GET', 'POST'])
def product_new():
    divisions = get_divisions_for_dropdown()
    if request.method == 'POST':
        data = {
            'productName': request.form.get('productName', '').strip(),
            'productUOM':  request.form.get('productUOM', '').strip(),
            'productHSN':  request.form.get('productHSN', '').strip(),
            'divisionID':  request.form.get('divisionID'),
        }
        if not data['productName'] or not data['divisionID']:
            flash('Product name and division are required.', 'error')
            return render_template('products/product_new.html', active_page='products', divisions=divisions)
        try:
            create_product(data)
            flash('Product created successfully.', 'success')
            return redirect(url_for('products.products'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('products/products_new.html', active_page='products', divisions=divisions)