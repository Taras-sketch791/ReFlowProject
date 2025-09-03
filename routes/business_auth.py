from flask import Blueprint, request, render_template, redirect, url_for, flash
from api_connect.business_auth import BusinessAuthClient
from api_connect.business_product import ProductClient
# Настройка логирования

# Создание Blueprint
business_auth_bp = Blueprint('business_auth', __name__,
                             template_folder='templates/business_auth',
                             static_folder='static/business_auth')

# Инициализация клиента
client = BusinessAuthClient()
product_client = ProductClient()


# HTML Endpoints
@business_auth_bp.route('/business-register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        data = {
            "inn": request.form.get('inn'),
            "email": request.form.get('email'),
            "title": request.form.get('title'),
            "password": request.form.get('password')
        }
        result = client.register_business(data)

        if result['status'] == 'success':
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('business_auth.login_page'))
        else:
            flash(result.get('detail', 'Ошибка при регистрации'), 'error')

    return render_template('business_auth/register.html')


@business_auth_bp.route('/business-login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = {
            "inn": request.form.get('inn'),
            "password": request.form.get('password')
        }
        result = client.login_business(data)

        if result['status'] == 'success':
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('business_auth.dashboard',
                                    business_id=result['data']['business_id']))
        else:
            flash(result.get('detail', 'Неверные учетные данные'), 'error')

    return render_template('business_auth/login.html')


@business_auth_bp.route('/business-dashboard/<int:business_id>')
def dashboard(business_id):
    products = product_client.get_business_products(business_id=business_id)["data"]
    result = client.get_business_info(business_id)

    if result['status'] == 'success':
        return render_template('business_auth/dashboard.html', business=result['data'], products=products, business_id=business_id)
    else:
        flash(result.get('detail', 'Ошибка при получении данных'), 'error')
        return redirect(url_for('business_auth.login_page', business_id=business_id))


@business_auth_bp.route('/business-delete/<int:business_id>', methods=['POST'])
def delete_page(business_id):
    result = client.delete_business(business_id)

    if result['status'] == 'success':
        flash('Аккаунт успешно удален', 'success')
        return redirect(url_for('business_auth.login_page'))
    else:
        flash(result.get('detail', 'Ошибка при удалении'), 'error')
        return redirect(url_for('business_auth.dashboard', business_id=business_id))


@business_auth_bp.route('/analytics', methods=['GET'])
def analytics():
    return render_template('business_auth/analytics.html')

@business_auth_bp.route('/products', methods=['GET'])
def products():
    return render_template('business_auth/products.html')

@business_auth_bp.route('/partners', methods=['GET'])
def partners():
    return render_template('business_auth/partners.html')

@business_auth_bp.route('/chats', methods=['GET'])
def chats():
    return render_template('business_auth/chats.html')

