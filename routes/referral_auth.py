from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from api_connect.referral_auth import ReferralAuthClient
from db_run import db

# Создание Blueprint
referral_auth_bp = Blueprint('referral_auth', __name__,
                             template_folder='templates/referral_auth',
                             static_folder='static/referral_auth')

# Инициализация клиента
client = ReferralAuthClient()


# HTML Endpoints
@referral_auth_bp.route('/referral-register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        data = {
            "phone": request.form.get('phone'),
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "password": request.form.get('password'),
        }

        if request.form.get('referral_code'):
            data["referral_code"] = request.form.get('referral_code')

        result = client.register_referral(data)
        # referral_id = db.insert(
        #     "referrals",
        #     {
        #         "email": request.form.get("email"),
        #         "password": request.form.get("password"),
        #         "name": request.form.get("name"),
        #         "phone": request.form.get("phone"),
        #         "referral_code": request.form.get("referral_code"),
        #     }, returning=True
        # )

        if result:
            flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
            return redirect(url_for('referral_auth.login_page'))
        else:
            flash('Ошибка при регистрации', 'error')
        # if result['status'] == 'success':
        #     flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        #     return redirect(url_for('referral_auth.login_page'))
        # else:
        #     flash(result.get('data', {}).get('detail', 'Ошибка при регистрации'), 'error')

    return render_template('referral_auth/register.html')


@referral_auth_bp.route('/referral-login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        data = {
            "phone": request.form.get('phone'),
            "password": request.form.get('password')
        }
        result = client.login_referral(data)

        if result['status'] == 'success':
            session['referral_id'] = result['data']['referral_id']
            session['phone'] = data['phone']
            flash('Вход выполнен успешно!', 'success')
            return redirect(url_for('referral_auth.dashboard',
                                    referral_id=result['data']['referral_id']))
        else:
            flash(result.get('data', {}).get('detail', 'Неверные учетные данные'), 'error')

    return render_template('referral_auth/login.html')


@referral_auth_bp.route('/referral-dashboard/<int:referral_id>')
def dashboard(referral_id):
    if 'referral_id' not in session or session['referral_id'] != referral_id:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('referral_auth.login_page'))

    result = client.get_referral_info(referral_id)

    if result['status'] == 'success':
        return render_template('referral_auth/dashboard.html', referral=result['data'], referral_id=referral_id)
    else:
        flash(result.get('data', {}).get('detail', 'Ошибка при получении данных'), 'error')
        return redirect(url_for('referral_auth.login_page'))


@referral_auth_bp.route('/referral-delete/<int:referral_id>', methods=['POST'])
def delete_page(referral_id):
    if 'referral_id' not in session or session['referral_id'] != referral_id:
        flash('Пожалуйста, войдите в систему', 'error')
        return redirect(url_for('referral_auth.login_page'))

    result = client.delete_referral(referral_id)

    if result['status'] == 'success':
        session.clear()
        flash('Аккаунт успешно деактивирован', 'success')
        return redirect(url_for('referral_auth.login_page'))
    else:
        flash(result.get('data', {}).get('detail', 'Ошибка при удалении'), 'error')
        return redirect(url_for('referral_auth.dashboard', referral_id=referral_id))


@referral_auth_bp.route('/referral-logout')
def logout():
    session.clear()
    flash('Вы успешно вышли из системы', 'success')
    return redirect(url_for('referral_auth.login_page'))