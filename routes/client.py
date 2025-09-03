from flask import Blueprint, render_template, session, redirect, url_for, flash, request, current_app
from db_run import db
from utils.qr_generator import generate_qr_code
import uuid
from werkzeug.security import check_password_hash
from datetime import datetime

client_bp = Blueprint('client', __name__, url_prefix='/client')

@client_bp.route('/dashboard')
def client_dashboard():
    if 'client_id' not in session:
        return redirect(url_for('auth.client_login'))

    businesses = db.fetch_all("SELECT * FROM business")
    return render_template('client/dashboard.html', businesses=businesses)


@client_bp.route('/products/<int:business_id>', methods=['GET', 'POST'])
def client_products(business_id):
    if 'client_id' not in session:
        return redirect(url_for('auth.client_login'))

    if request.method == 'POST':
        # Обработка создания ссылки
        product_id = request.form.get('product_id')
        product = db.fetch_one("SELECT * FROM products WHERE id = %s", (product_id,))

        if not product:
            flash('Товар не найден', 'error')
            return redirect(url_for('client.client_dashboard'))

        # Проверяем существующую ссылку
        existing_link = db.fetch_one(
            "SELECT * FROM referrals WHERE client_id = %s AND product_id = %s",
            (session['client_id'], product_id))

        if not existing_link:
            # Создаем новую ссылку
            referral_code = str(uuid.uuid4())[:8]
            referral_link = f"{request.host_url}r/{referral_code}"
            qr_code = generate_qr_code(referral_link)

            db.insert('referrals', {
                'client_id': session['client_id'],
                'product_id': product_id,
                'code': referral_code,
                'link': referral_link,
                'qr_code': qr_code,
                'created_at': datetime.now()
            })
            flash('Реферальная ссылка создана!', 'success')
        else:
            flash('Реферальная ссылка уже существует', 'info')

        return redirect(url_for('client.client_products', business_id=business_id))

    # GET запрос - показываем товары
    business = db.fetch_one("SELECT * FROM business WHERE id = %s", (business_id,))
    if not business:
        flash('Бизнес не найден', 'error')
        return redirect(url_for('client.client_dashboard'))

    products = db.fetch_all("""
        SELECT p.*, 
               r.id as referral_id,
               r.link as referral_link,
               r.qr_code as referral_qr
        FROM products p
        LEFT JOIN referrals r ON r.product_id = p.id AND r.client_id = %s
        WHERE p.business_id = %s
    """, (session['client_id'], business_id))

    return render_template('client/products.html',
                         business=business,
                         products=products)


@client_bp.route('/referrals/<int:product_id>')
def view_referral(product_id):
    if 'client_id' not in session:
        return redirect(url_for('auth.client_login'))

    referral = db.fetch_one("""
        SELECT r.*, 
               p.title as product_name,
               p.business_id,
               b.title as business_name
        FROM referrals r
        JOIN products p ON r.product_id = p.id
        JOIN business b ON p.business_id = b.id
        WHERE r.client_id = %s AND r.product_id = %s
    """, (session['client_id'], product_id))

    if not referral:
        flash('Реферальная ссылка не найдена', 'error')
        return redirect(url_for('client.client_dashboard'))
    telegram_link = f"https://t.me/seller1_demo_bot?start=ref_{referral['code']}"
    telegram_qr = generate_qr_code(telegram_link)

    return render_template('client/referral_details.html',
                           referral=referral,
                           telegram_link=telegram_link,
                           telegram_qr=telegram_qr)
# Добавить другие клиентские маршруты (profile, settings, withdraw)

# Профиль клиента
@client_bp.route('/profile')
def client_profile():
    if 'client_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('auth.client_login'))

    try:
        # Получаем данные клиента
        client = db.fetch_one(
            """SELECT id, name, email, phone, payment_details, created_at 
            FROM clients WHERE id = %s""",
            (session['client_id'],))

        if not client:
            flash('Профиль не найден', 'error')
            return redirect(url_for('auth.client_login'))

        # Получаем статистику
        stats = db.fetch_one("""
            SELECT 
                COUNT(r.id) as referrals_count,
                COUNT(CASE WHEN rc.id IS NOT NULL THEN 1 END) as clicks_count,
                COALESCE(SUM(p.price * p.referral_percent / 100), 0) as total_earnings,
                COALESCE(SUM(CASE WHEN wr.status = 'completed' THEN wr.amount ELSE 0 END), 0) as withdrawn_amount
            FROM referrals r
            JOIN products p ON r.product_id = p.id
            LEFT JOIN referral_clicks rc ON r.id = rc.referral_id
            LEFT JOIN withdrawal_requests wr ON wr.client_id = %s
            WHERE r.client_id = %s
        """, (session['client_id'], session['client_id']))

        # Получаем последние реферальные ссылки
        recent_links = db.fetch_all("""
            SELECT r.*, p.title as product_name, p.image as product_image
            FROM referrals r
            JOIN products p ON r.product_id = p.id
            WHERE r.client_id = %s
            ORDER BY r.created_at DESC
            LIMIT 5
        """, (session['client_id'],))

        return render_template('client/profile.html',
                               client=client,
                               stats=stats,
                               recent_links=recent_links)

    except Exception as e:
        current_app.logger.error(f"Ошибка загрузки профиля: {str(e)}")
        flash('Ошибка загрузки профиля', 'error')
        return redirect(url_for('client.client_dashboard'))


# Создание реферальной ссылки
@client_bp.route('/create-link/<int:product_id>', methods=['GET', 'POST'])
def create_link(product_id):
    if 'client_id' not in session:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('auth.client_login'))
    try:
        # Проверяем существование продукта
        product = db.fetch_one(
            "SELECT * FROM products WHERE id = %s",
            (product_id,))
        if not product:
            flash('Товар не найден', 'error')
            return redirect(url_for('client.client_dashboard'))
        if request.method == 'POST':
            existing_link = db.fetch_one(
                "SELECT id FROM referrals WHERE client_id = %s AND product_id = %s",
                (session['client_id'], product_id))
            if existing_link:
                flash('Вы уже создавали ссылку для этого товара', 'info')
                return redirect(url_for('client.client_profile'))
            # Генерация уникального кода
            referral_code = str(uuid.uuid4())[:8]
            referral_link = f"{request.host_url}r/{referral_code}"
            # Генерация QR-кода
            qr_code = generate_qr_code(referral_link)
            # Сохранение в БД
            db.insert('referrals', {
                'client_id': session['client_id'],
                'product_id': product_id,
                'code': referral_code,
                'link': referral_link,
                'qr_code': qr_code,
                'created_at': datetime.now()
            })

            flash('Реферальная ссылка успешно создана!', 'success')
            return redirect(url_for('client.client_profile'))

        # Для GET-запроса показываем страницу с подтверждением
        return render_template('client/create_link.html',
                               product=product)

    except Exception as e:
        current_app.logger.error(f"Ошибка создания ссылки: {str(e)}")
        flash('Ошибка создания реферальной ссылки', 'error')
        return redirect(url_for('client.client_dashboard'))


@client_bp.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'client_id' not in session:
        return redirect(url_for('auth.client_login'))

    if request.method == 'POST':
        amount = float(request.form.get('amount'))
        payment_method = request.form.get('payment_method')

        # Проверка баланса и сохранение запроса
        # ...

    return render_template('client/withdraw.html')