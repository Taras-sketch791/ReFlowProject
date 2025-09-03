from flask import Blueprint, render_template, request, redirect, url_for, flash

from api_connect.business_product import ProductClient

product_bp = Blueprint('product_bus', __name__, url_prefix='/product_bus')

client = ProductClient()


@product_bp.route('business/product_list/<int:business_id>')
def list_products(business_id):
    """Display all products for a business"""
    if not business_id:
        flash('Business ID is required', 'error') # Redirect to appropriate page

    response = client.get_business_products(business_id)

    if response['status'] == 'error':
        flash(f"Failed to fetch products: {response.get('detail', 'Unknown error')}", 'error')
        return render_template('business_auth/products.html', products=[], business_id=business_id)

    return render_template('business_auth/products.html',
                           products=response['data'],
                           business_id=business_id)


@product_bp.route('business/create/<int:business_id>', methods=['GET', 'POST'])
def create_product(business_id):
    """Create a new product"""
    if not business_id:
        flash('Business ID is required', 'error')

    if request.method == 'POST':
        # Collect form data
        product_data = {
            'business_id': business_id,
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price', 0)),
            'link2product': request.form.get('link2product'),
            'image': request.form.get('image'),
            'payment_method_id': request.form.get('payment_method_id', type=int),
            'payment_requirements': request.form.get('payment_requirements'),
            'is_available': request.form.get('is_available') == 'on'
        }

        # Create product via API
        response = client.create_product(**product_data)

        if response['status'] == 'success':
            flash('Product created successfully!', 'success')
            return redirect(url_for('product_bus.list_products', business_id=business_id))
        else:
            flash(f"Failed to create product: {response.get('detail', 'Unknown error')}", 'error')
    return render_template('business_product/create.html', business_id=business_id)


@product_bp.route('/<int:product_id>')
def view_product(product_id):
    business_id = request.args.get('business_id', type=int)
    """View product details"""
    response = client.get_product(product_id)

    if response['status'] == 'error':
        flash(f"Failed to fetch product: {response.get('detail', 'Unknown error')}", 'error')
        return redirect(url_for('product_bus.list_products'))

    return render_template('business_product/view.html', product=response['data'], business_id=business_id)


@product_bp.route('/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    business_id = request.args.get('business_id', type=int)
    """Edit product details"""
    if request.method == 'POST':
        # Collect form data
        update_data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'price': request.form.get('price', type=float),
            'referral_percent': request.form.get('referral_percent', type=float),
            'link2product': request.form.get('link2product'),
            'image': request.form.get('image'),
            'payment_method_id': request.form.get('payment_method_id', type=int),
            'payment_requirements': request.form.get('payment_requirements'),
            'is_available': request.form.get('is_available') == 'on'
        }

        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}

        # Update product via API
        response = client.update_product(product_id, **update_data)

        if response['status'] == 'success':
            flash('Product updated successfully!', 'success')
            return redirect(url_for('product.view_product', product_id=product_id))
        else:
            flash(f"Failed to update product: {response.get('detail', 'Unknown error')}", 'error')

    # GET request - load current product data
    response = client.get_product(product_id)

    if response['status'] == 'error':
        flash(f"Failed to fetch product: {response.get('detail', 'Unknown error')}", 'error')
        return redirect(url_for('product.list_products'))

    return render_template('business_product/edit.html', product=response['data'], business_id=business_id)


@product_bp.route('/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    """Delete a product"""
    response = client.delete_product(product_id)

    if response['status'] == 'success':
        flash('Product deleted successfully!', 'success')
    else:
        flash(f"Failed to delete product: {response.get('detail', 'Unknown error')}", 'error')

    return redirect(url_for('product.list_products'))
