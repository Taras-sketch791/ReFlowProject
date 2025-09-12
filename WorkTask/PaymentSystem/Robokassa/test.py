from client import RobokassaClient
from models import HashAlgorithm


robokassa = RobokassaClient(
    merchant_login="reflow",
    password1="test_key_1",
    password2="test_key_2",
    is_test=True,
    algorithm=HashAlgorithm.MD5,
)

link = robokassa.get_payment_url(1, 100, "Тестовая оплата")
print(link)
