from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from api_connect.business_product import ProductClient
from api_connect.referral_auth import ReferralAuthClient
from api_connect.referral_request_bus import ReferralStatusClient
from api_connect.referral_links import ReferralLinkClient

import random
from datetime import datetime, timedelta
import json

referral_bp = Blueprint('referral_products', __name__, url_prefix='/referral_products')

client = ProductClient()
referral_client = ReferralAuthClient()
ref_req_client = ReferralStatusClient()
ref_link_client = ReferralLinkClient()


def generate_orders(count=20):
    products = [
        {
            "name": "Смартфон Premium X",
            "description": "Флагманский смартфон с улучшенной камерой",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop",
            "base_price": 34990
        },
        {
            "name": "Ноутбук Gaming Pro",
            "description": "Мощный игровой ноутбук с RTX 4070",
            "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=300&fit=crop",
            "base_price": 129990
        },
        {
            "name": "Беспроводные наушники",
            "description": "Наушники с шумоподавлением",
            "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop",
            "base_price": 8990
        },
        {
            "name": "Умные часы Fitness",
            "description": "Часы с отслеживанием активности",
            "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop",
            "base_price": 15990
        }
    ]

    statuses = ['new', 'processing', 'completed', 'cancelled']
    orders = []

    for i in range(count):
        product = random.choice(products)
        quantity = random.randint(1, 3)
        price = product['base_price'] * quantity
        commission = round(price * random.uniform(0.05, 0.15), 2)

        order = {
            "id": i + 1,
            "title": product['name'],
            "description": product['description'],
            "image": product['image'],
            "price": price,
            "quantity": quantity,
            "status": random.choice(statuses),
            "date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "orderNumber": f"#ORD-{1000 + i}",
            "commission": commission
        }
        orders.append(order)

    return orders


# Кэшируем данные для быстрого доступа
# orders_cache = generate_orders(50)


# @referral_bp.route('/partner/orders')
# def partner_orders():
#     return render_template('referral_products/show_cards.html')


# @referral_bp.route('/api/orders')
# def get_orders():
#     page = int(request.args.get('page', 1))
#     status = request.args.get('status', 'all')
#     sort = request.args.get('sort', 'newest')
#     per_page = 12
#
#     # Фильтрация по статусу
#     filtered_orders = orders_cache
#     if status != 'all':
#         filtered_orders = [order for order in orders_cache if order['status'] == status]
#
#     # Сортировка
#     if sort == 'newest':
#         filtered_orders.sort(key=lambda x: x['date'], reverse=True)
#     elif sort == 'oldest':
#         filtered_orders.sort(key=lambda x: x['date'])
#     elif sort == 'price':
#         filtered_orders.sort(key=lambda x: x['price'], reverse=True)
#     elif sort == 'commission':
#         filtered_orders.sort(key=lambda x: x['commission'], reverse=True)
#
#     # Пагинация
#     start_idx = (page - 1) * per_page
#     end_idx = start_idx + per_page
#     paginated_orders = filtered_orders[start_idx:end_idx]
#
#     return jsonify({
#         'orders': paginated_orders,
#         'total': len(filtered_orders),
#         'page': page,
#         'per_page': per_page,
#         'total_pages': (len(filtered_orders) + per_page - 1) // per_page
#     })


# @referral_bp.route('/api/orders/stats')
# def get_orders_stats():
#     status_count = {
#         'new': len([o for o in orders_cache if o['status'] == 'new']),
#         'processing': len([o for o in orders_cache if o['status'] == 'processing']),
#         'completed': len([o for o in orders_cache if o['status'] == 'completed']),
#         'cancelled': len([o for o in orders_cache if o['status'] == 'cancelled']),
#         'total': len(orders_cache)
#     }
#
#     total_commission = sum(order['commission'] for order in orders_cache)
#     total_revenue = sum(order['price'] for order in orders_cache)
#
#     return jsonify({
#         'status_count': status_count,
#         'total_commission': total_commission,
#         'total_revenue': total_revenue
#     })


@referral_bp.route('<int:referral_id>/businesses')
def list_businesses(referral_id):
    """Display all available businesses for referral"""
    try:
        ref_data = referral_client.get_referral_info(referral_id)

        # Получаем список бизнесов через API
        response = client.get_businesses()

        if response['status'] == 'error':
            flash(f"Failed to fetch businesses: {response.get('detail', 'Unknown error')}", 'error')
            return render_template('referral_products/businesses.html', businesses=[],
                                   referral_id=referral_id, ref_data=ref_data)

        return render_template('referral_products/businesses.html', businesses=response['data'],
                               ref_data=ref_data, referral_id=referral_id)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return render_template('referral_products/businesses.html', businesses=[],
                               referral_id=referral_id, ref_data={})


@referral_bp.route('<int:referral_id>/business/<int:business_id>/products')
def business_products(referral_id, business_id):
    """Display products for a specific business"""
    try:
        # Получаем информацию о бизнесе
        business_response = client.get_business(business_id)
        ref_data = referral_client.get_referral_info(referral_id)

        if business_response['status'] == 'error':
            flash(f"Failed to fetch business info: {business_response.get('detail', 'Unknown error')}", 'error')
            return redirect(url_for('referral_products.list_businesses', referral_id=referral_id))

        # Получаем продукты бизнеса
        products_response = client.get_business_products(business_id)

        if products_response['status'] == 'error':
            flash(f"Failed to fetch products: {products_response.get('detail', 'Unknown error')}", 'error')
            return render_template('referral_products/business_products.html',
                                   business=business_response['data'],
                                   products=[],
                                   ref_data=ref_data,
                                   referral_id=referral_id)

        return render_template('referral_products/business_products.html',
                               business=business_response['data'],
                               products=products_response['data'],
                               ref_data=ref_data,
                               referral_id=referral_id)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('referral_products.list_businesses', referral_id=referral_id))


@referral_bp.route('<int:referral_id>/product/<int:product_id>')
def view_product(referral_id, product_id):
    """View product details with referral options"""
    try:
        # Получаем информацию о продукте
        product_response = client.get_product(product_id)
        ref_data = referral_client.get_referral_info(referral_id)

        if product_response['status'] == 'error':
            flash(f"Failed to fetch product: {product_response.get('detail', 'Unknown error')}", 'error')
            return redirect(url_for('referral_products.list_businesses', referral_id=referral_id))

        # Получаем информацию о бизнесе
        business_response = client.get_business(product_response['data']['business_id'])

        if business_response['status'] == 'error':
            flash(f"Failed to fetch business info: {business_response.get('detail', 'Unknown error')}", 'error')

        # Проверяем статус заявки реферала
        status_response = ref_req_client.get_status_referral(
            business_id=product_response['data']['business_id'],
            referral_id=referral_id
        )

        is_approved = status_response.get('data', {}).get('status') == 'approved'
        referral_link = None
        qr_code = None
        existing_link = None
        telegram_link = None
        telegram_qr = None

        # Если заявка принята, получаем или создаем реферальную ссылку
        if is_approved:
            # Используем новую функцию get_or_create_referral_link
            link_response = ref_link_client.get_or_create_referral_link(
                client_id=ref_data['data']['id'],
                product_id=product_id
            )

            if link_response['status'] == 'success':
                link_data = link_response['data']
                if isinstance(link_data, list) and len(link_data) > 0:
                    # Если вернулся список, берем первую ссылку
                    existing_link = link_data[0]
                elif isinstance(link_data, dict):
                    # Если вернулся объект с данными
                    existing_link = link_data.get('data')

                if existing_link:
                    referral_link = existing_link.get('link')
                    qr_code = existing_link.get('qr_code')
                    telegram_link = existing_link.get('telegram_link')
                    telegram_qr = existing_link.get('telegram_qr')

        return render_template('referral_products/view_product.html',
                               product=product_response['data'],
                               business=business_response.get('data', {}),
                               ref_data=ref_data,
                               referral_id=referral_id,
                               is_approved=is_approved,
                               referral_link=referral_link,
                               qr_code=qr_code,
                               telegram_link=telegram_link,
                               telegram_qr=telegram_qr
                               )

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('referral_products.list_businesses', referral_id=referral_id))


@referral_bp.route('<int:referral_id>/product/<int:product_id>/generate-link', methods=['POST'])
def generate_referral_link(referral_id, product_id):
    """Generate referral link for a specific product"""
    try:
        ref_data = referral_client.get_referral_info(referral_id)

        # Создаем реферальную ссылку через API
        link_response = ref_link_client.get_or_create_referral_link(
            client_id=ref_data['data']['id'],
            product_id=product_id
        )

        if link_response['status'] == 'success':
            flash("Реферальная ссылка успешно создана!", 'success')
        else:
            flash(f"Ошибка создания ссылки: {link_response.get('detail', 'Unknown error')}", 'error')

    except Exception as e:
        flash(f"Произошла ошибка: {str(e)}", 'error')

    return redirect(url_for('referral_products.view_product',
                            referral_id=referral_id, product_id=product_id))


@referral_bp.route('/<int:business_id>/<int:referral_id>/request', methods=['GET', 'POST'])
def request_partnership(business_id, referral_id):
    """Request partnership with business"""
    try:
        response = ref_req_client.create_status(
            business_id=business_id,
            referral_id=referral_id,
            status='pending'
        )

        if response.get('status') == 'success':
            flash('Запрос на сотрудничество успешно отправлен!', 'success')
        else:
            flash(f'Ошибка при отправке запроса: {response.get("detail", "Неизвестная ошибка")}', 'error')

    except Exception as e:
        flash(f'Произошла ошибка: {str(e)}', 'error')

    return redirect(url_for('referral_products.business_products',
                            business_id=business_id,
                            referral_id=referral_id))


@referral_bp.route('<int:referral_id>/my-links')
def my_referral_links(referral_id):
    """Display all referral links for the current user"""
    try:
        ref_data = referral_client.get_referral_info(referral_id)

        # Получаем все продукты для отображения информации
        products_response = ref_link_client.get_referral_link_by_client(client_id=referral_id)
        products_dict = {}
        if products_response['status'] == 'success':
            for product in products_response['data']:
                products_dict[product['id']] = product

        # Получаем все ссылки пользователя
        # Для этого нужно сначала получить все бизнесы, затем продукты, затем ссылки
        # Или добавить новый endpoint в API для получения всех ссылок пользователя

        businesses_response = client.get_businesses()
        user_links = []

        if businesses_response['status'] == 'success':
            for business in businesses_response['data']:
                products_response = client.get_business_products(business['id'])
                if products_response['status'] == 'success':
                    for product in products_response['data']:
                        # Проверяем есть ли ссылка для этого продукта
                        link_response = ref_link_client.check_referral_link_by_client_product(
                            client_id=ref_data['data']['id'],
                            product_id=product['id']
                        )
                        if link_response['status'] == 'success' and link_response['data']['exists']:
                            # Получаем полную информацию о ссылке
                            full_link_response = ref_link_client.get_or_create_referral_link(
                                client_id=ref_data['data']['id'],
                                product_id=product['id']
                            )
                            if full_link_response['status'] == 'success':
                                link_data = full_link_response['data']
                                link_data['product_name'] = product['name']
                                link_data['business_name'] = business['name']
                                user_links.append(link_data)

        return render_template('referral_products/my_links.html',
                               links=user_links,
                               ref_data=ref_data,
                               referral_id=referral_id)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('referral_products.list_businesses', referral_id=referral_id))


@referral_bp.route('/partner/orders')
def get_orders():
    # Пример данных заказов
    orders = [
        {
            "id": 1,
            "title": "Смартфон Premium X",
            "description": "Флагманский смартфон с улучшенной камерой и долгим временем работы от аккумулятора",
            "image": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=400&h=300&fit=crop",
            "price": 34990,
            "commission": 1749,
            "quantity": 1,
            "status": "new",
            "created_date": "15.01.2024"
        },
        {
            "id": 2,
            "title": "Ноутбук Gaming Pro",
            "description": "Мощный игровой ноутбук с видеокартой RTX 4070 и процессором Intel i9",
            "image": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=300&fit=crop",
            "price": 129990,
            "commission": 6499,
            "quantity": 1,
            "status": "new",
            "created_date": "14.01.2024"
        },
        {
            "id": 3,
            "title": "Беспроводные наушники",
            "description": "Качественные беспроводные наушники с шумоподавлением",
            "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop",
            "price": 8990,
            "commission": 449,
            "quantity": 2,
            "status": "processing",
            "created_date": "12.01.2024"
        }
    ]

    total_commission = sum(order['commission'] for order in orders)

    return render_template('referral_products/partner_orders.html',
                           orders=orders,
                           total_commission=total_commission)