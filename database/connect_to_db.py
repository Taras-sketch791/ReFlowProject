from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DECIMAL, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import os

# Данные для подключения
DB_CONFIG = {
    'dbname': 'reflow_testing',
    'user': 'reflow_user',
    'password': 'reflow_password123',
    'host': '193.162.143.84',
    'port': '5432',
}

# Создание строки подключения
DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"

# Создание engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True для отладки SQL запросов

# Создание метаданных
metadata = MetaData()

# Определение существующих таблиц
api_keys = Table(
    'api_keys', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(255), nullable=False),
    Column('api_key', String(255), nullable=False),
)

cards = Table(
    'cards', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(255), nullable=False),
    Column('description', Text),
    Column('price', DECIMAL(10, 2)),
)

# Определение таблиц Wildberries
wb_accounts = Table(
    'wb_accounts', metadata,
    Column('id', Integer, primary_key=True),
    Column('api_key', String(255), nullable=False, unique=True),
    Column('account_name', String(100), nullable=False),
    Column('company_name', String(100)),
    Column('is_active', Boolean, default=True),
    Column('created_at', TIMESTAMP, default=func.current_timestamp()),
    Column('last_sync', TIMESTAMP)
)

wb_cards = Table(
    'wb_cards', metadata,
    Column('id', Integer, primary_key=True),
    Column('account_id', Integer, ForeignKey('wb_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('nm_id', Integer, nullable=False),  # Артикул WB
    Column('sku', String(100)),  # Артикул продавца
    Column('imt_name', String(500)),  # Название карточки
    Column('subject_name', String(200)),  # Категория
    Column('brand_name', String(200)),  # Бренд
    Column('current_price', DECIMAL(10, 2)),
    Column('original_price', DECIMAL(10, 2)),
    Column('total_quantity', Integer, default=0),
    Column('created_at', TIMESTAMP, default=func.current_timestamp()),
    Column('updated_at', TIMESTAMP, default=func.current_timestamp())
)

wb_sizes = Table(
    'wb_sizes', metadata,
    Column('id', Integer, primary_key=True),
    Column('card_id', Integer, ForeignKey('wb_cards.id', ondelete='CASCADE'), nullable=False),
    Column('size_name', String(50), nullable=False),
    Column('size_sku', String(100)),
    Column('quantity', Integer, default=0),
    Column('barcode', String(100))
)

wb_images = Table(
    'wb_images', metadata,
    Column('id', Integer, primary_key=True),
    Column('card_id', Integer, ForeignKey('wb_cards.id', ondelete='CASCADE'), nullable=False),
    Column('image_url', Text, nullable=False),
    Column('sort_order', Integer, default=0)
)

sync_logs = Table(
    'sync_logs', metadata,
    Column('id', Integer, primary_key=True),
    Column('account_id', Integer, ForeignKey('wb_accounts.id', ondelete='CASCADE'), nullable=False),
    Column('status', String(20), nullable=False),
    Column('cards_processed', Integer, default=0),
    Column('error_message', Text),
    Column('sync_date', TIMESTAMP, default=func.current_timestamp())
)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()

def connection():
    """Тестирование подключения к базе данных"""
    try:
        with engine.connect() as conn:
            print("✅ Успешное подключение к базе данных!")
            return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def get_all_cards():
    """Получение всех карточек"""
    try:
        with engine.connect() as conn:
            result = conn.execute(cards.select())
            return result.fetchall()
    except Exception as e:
        print(f"Ошибка при получении карточек: {e}")
        return []

def insert_card(title, description, price):
    """Добавление новой карточки"""
    try:
        with engine.connect() as conn:
            stmt = cards.insert().values(
                title=title,
                description=description,
                price=price
            )
            result = conn.execute(stmt)
            conn.commit()
            print(f"✅ Карточка добавлена с ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        print(f"Ошибка при добавлении карточки: {e}")
        return None

def get_api_keys():
    """Получение всех API ключей"""
    try:
        with engine.connect() as conn:
            result = conn.execute(api_keys.select())
            return result.fetchall()
    except Exception as e:
        print(f"Ошибка при получении API ключей: {e}")
        return []

# Функции для работы с таблицами Wildberries
def add_wb_account(api_key, account_name, company_name=None, is_active=True):
    """Добавление аккаунта Wildberries"""
    try:
        with engine.connect() as conn:
            stmt = wb_accounts.insert().values(
                api_key=api_key,
                account_name=account_name,
                company_name=company_name,
                is_active=is_active
            )
            result = conn.execute(stmt)
            conn.commit()
            print(f"✅ Аккаунт WB добавлен с ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        print(f"Ошибка при добавлении аккаунта WB: {e}")
        return None

def get_wb_accounts(active_only=True):
    """Получение всех аккаунтов Wildberries"""
    try:
        with engine.connect() as conn:
            query = wb_accounts.select()
            if active_only:
                query = query.where(wb_accounts.c.is_active == True)
            result = conn.execute(query)
            return result.fetchall()
    except Exception as e:
        print(f"Ошибка при получении аккаунтов WB: {e}")
        return []

def add_wb_card(account_id, nm_id, sku=None, imt_name=None, subject_name=None, 
                brand_name=None, current_price=None, original_price=None, total_quantity=0):
    """Добавление карточки товара Wildberries"""
    try:
        with engine.connect() as conn:
            stmt = wb_cards.insert().values(
                account_id=account_id,
                nm_id=nm_id,
                sku=sku,
                imt_name=imt_name,
                subject_name=subject_name,
                brand_name=brand_name,
                current_price=current_price,
                original_price=original_price,
                total_quantity=total_quantity
            )
            result = conn.execute(stmt)
            conn.commit()
            print(f"✅ Карточка WB добавлена с ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        print(f"Ошибка при добавлении карточки WB: {e}")
        return None

def get_wb_cards_by_account(account_id):
    """Получение карточек товаров по аккаунту"""
    try:
        with engine.connect() as conn:
            query = wb_cards.select().where(wb_cards.c.account_id == account_id)
            result = conn.execute(query)
            return result.fetchall()
    except Exception as e:
        print(f"Ошибка при получении карточек WB: {e}")
        return []

def add_wb_size(card_id, size_name, size_sku=None, quantity=0, barcode=None):
    """Добавление размера товара"""
    try:
        with engine.connect() as conn:
            stmt = wb_sizes.insert().values(
                card_id=card_id,
                size_name=size_name,
                size_sku=size_sku,
                quantity=quantity,
                barcode=barcode
            )
            result = conn.execute(stmt)
            conn.commit()
            print(f"✅ Размер добавлен с ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        print(f"Ошибка при добавлении размера: {e}")
        return None

def add_wb_image(card_id, image_url, sort_order=0):
    """Добавление изображения товара"""
    try:
        with engine.connect() as conn:
            stmt = wb_images.insert().values(
                card_id=card_id,
                image_url=image_url,
                sort_order=sort_order
            )
            result = conn.execute(stmt)
            conn.commit()
            print(f"✅ Изображение добавлено с ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        print(f"Ошибка при добавлении изображения: {e}")
        return None

def add_sync_log(account_id, status, cards_processed=0, error_message=None):
    """Добавление записи в лог синхронизации"""
    try:
        with engine.connect() as conn:
            stmt = sync_logs.insert().values(
                account_id=account_id,
                status=status,
                cards_processed=cards_processed,
                error_message=error_message
            )
            result = conn.execute(stmt)
            conn.commit()
            print(f"✅ Лог синхронизации добавлен с ID: {result.inserted_primary_key[0]}")
            return result.inserted_primary_key[0]
    except Exception as e:
        print(f"Ошибка при добавлении лога синхронизации: {e}")
        return None

def get_sync_logs(account_id=None, limit=10):
    """Получение логов синхронизации"""
    try:
        with engine.connect() as conn:
            query = sync_logs.select()
            if account_id:
                query = query.where(sync_logs.c.account_id == account_id)
            query = query.order_by(sync_logs.c.sync_date.desc()).limit(limit)
            result = conn.execute(query)
            return result.fetchall()
    except Exception as e:
        print(f"Ошибка при получении логов синхронизации: {e}")
        return []

def update_wb_account_last_sync(account_id):
    """Обновление времени последней синхронизации аккаунта"""
    try:
        with engine.connect() as conn:
            stmt = wb_accounts.update().where(wb_accounts.c.id == account_id).values(
                last_sync=func.current_timestamp()
            )
            conn.execute(stmt)
            conn.commit()
            print(f"✅ Время синхронизации обновлено для аккаунта {account_id}")
            return True
    except Exception as e:
        print(f"Ошибка при обновлении времени синхронизации: {e}")
        return False

# Пример использования
if __name__ == "__main__":
    # Тестируем подключение
    connection()

    # Получаем все карточки
    print("\n📋 Все карточки:")
    all_cards = get_all_cards()
    for card in all_cards:
        print(card)

    # Получаем API ключи
    print("\n🔑 API ключи:")
    api_keys_list = get_api_keys()
    for key in api_keys_list:
        print(key)

    # Добавляем новую карточку
    new_card_id = insert_card(
        title="Новая карточка из Python",
        description="Создана через SQLAlchemy",
        price=1999.99,
    )

    # Пример работы с таблицами Wildberries
    print("\n🛍️ Работа с Wildberries:")
    
    # Добавляем аккаунт WB
    account_id = add_wb_account(
        api_key="your_wb_api_key_here",
        account_name="Мой магазин WB",
        company_name="ООО Мой бизнес"
    )
    
    if account_id:
        # Добавляем карточку товара
        card_id = add_wb_card(
            account_id=account_id,
            nm_id=123456789,
            sku="MY_SKU_001",
            imt_name="Футболка мужская",
            subject_name="Футболки",
            brand_name="Мой бренд",
            current_price=1999.99,
            original_price=2499.99,
            total_quantity=100
        )
        
        if card_id:
            # Добавляем размеры
            add_wb_size(
                card_id=card_id,
                size_name="M",
                size_sku="MY_SKU_001_M",
                quantity=50,
                barcode="1234567890123"
            )
            
            # Добавляем изображения
            add_wb_image(
                card_id=card_id,
                image_url="https://example.com/image1.jpg",
                sort_order=1
            )
        
        # Добавляем лог синхронизации
        add_sync_log(
            account_id=account_id,
            status="success",
            cards_processed=1
        )
        
        # Обновляем время синхронизации
        update_wb_account_last_sync(account_id)
        
        # Получаем карточки аккаунта
        print(f"\n📦 Карточки аккаунта {account_id}:")
        wb_cards_list = get_wb_cards_by_account(account_id)
        for card in wb_cards_list:
            print(card)
    
    # Получаем логи синхронизации
    print("\n📊 Логи синхронизации:")
    logs = get_sync_logs(limit=5)
    for log in logs:
        print(log)
