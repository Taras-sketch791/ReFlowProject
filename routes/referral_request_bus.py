from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from api_connect.referral_request_bus import ReferralStatusClient

referrals_bp = Blueprint('referral_request_bus', __name__, url_prefix='/referral_request_bus')

# Инициализация клиента для работы с API реферальных запросов
referral_client = ReferralStatusClient()


# Фильтры для Jinja2
@referrals_bp.app_template_filter('status_display')
def status_display_filter(status):
    status_map = {
        'pending': 'Ожидает',
        'accepted': 'Принят',
        'rejected': 'Отклонен'
    }
    return status_map.get(status, status)


@referrals_bp.app_template_filter('datetime_format')
def datetime_format_filter(value):
    if value is None:
        return ''
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").strftime('%d.%m.%Y %H:%M')


@referrals_bp.route('/<int:business_id>')
def index(business_id):
    if not business_id or business_id <= 0:
        flash('Неверный ID бизнеса', 'danger')
        return render_template('referrals/index.html', referrals=[])
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')

    # Получаем статусы для текущего бизнеса
    response = referral_client.get_business_statuses(business_id)

    if response['status'] == 'error':
        flash('Ошибка при загрузке реферальных запросов', 'danger')
        return render_template('referral_request_bus/index.html', referrals=[], page=1, total_pages=1,
                               current_status=status_filter)

    # Фильтрация по статусу
    referrals = response['data']
    if status_filter != 'all':
        referrals = [r for r in referrals if r['status'] == status_filter]

    # Пагинация (упрощенная реализация)
    per_page = 10
    total_items = len(referrals)
    total_pages = (total_items + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated_referrals = referrals[start_idx:end_idx]

    return render_template(
        'referral_request_bus/index.html',
        referrals=paginated_referrals,
        page=page,
        total_pages=total_pages,
        current_status=status_filter,
        business_id=business_id
    )


@referrals_bp.route('/<int:business_id>/<int:referral_id>/accept', methods=['POST'])
def accept(business_id, referral_id):
    response = referral_client.update_status(referral_id, status='approved', message="Approved")
    # response = referral_client.update_status(referral_id, status='accepted')
    print(response)
    if response['status'] == 'success':
        flash('Запрос принят', 'success')
    else:
        flash('Ошибка принятия', 'danger')

    return redirect(url_for('referral_request_bus.index', business_id=business_id))


@referrals_bp.route('/<int:business_id>/<int:referral_id>/reject', methods=['POST'])
def reject(business_id, referral_id):
    response = referral_client.update_status(referral_id, status='rejected', message="Rejected")

    if response['status'] == 'success':
        flash('Запрос отклонен', 'success')
    else:
        error_msg = response.get('detail', 'Не удалось отклонить запрос')
        flash(f'Ошибка: {error_msg}', 'danger')

    return redirect(url_for('referral_request_bus.index', business_id=business_id))


@referrals_bp.route('/<int:business_id>/<int:referral_id>/cancel', methods=['POST'])
def cancel_accept(business_id, referral_id):
    response = referral_client.update_status(referral_id, status='pending', message="Return to pending")

    if response['status'] == 'success':
        flash('Принятие запроса отменено', 'success')
    else:
        error_msg = response.get('detail', 'Не удалось отменить принятие')
        flash(f'Ошибка: {error_msg}', 'danger')

    return redirect(url_for('referral_request_bus.index', business_id=business_id))


@referrals_bp.route('/<int:business_id>/<int:referral_id>')
def details(business_id, referral_id):
    response = referral_client.get_status(referral_id)

    if response['status'] == 'error':
        flash('Запрос не найден', 'danger')
        return redirect(url_for('referral_request_bus.index'))

    referral = response['data']

    # # Проверка, что запрос принадлежит текущему бизнесу
    # if referral.get('business_id') != current_user.id:
    #     flash('Доступ запрещен', 'danger')
    # return redirect(url_for('referral_request_bus.index'))

    return render_template('referral_request_bus/details.html', referral=referral, business_id=business_id)