from robokassa import HashAlgorithm, Robokassa
import decimal
from decimal import Decimal 
import hashlib
from urllib import parse
from urllib.parse import urlparse
import logging

'''
test_key_1 = "w7uCkP2G7m3HP4jyfdzP"
test_key_2 = "hfvx88t25kkbW8xbxUAh"

robokassa = Robokassa(
    merchant_login="reflow",
    password1=test_key_1,
    password2=test_key_2,
    is_test=True,
    algorithm=HashAlgorithm.md5,
)

my_link = robokassa.generate_open_payment_link(out_sum=100, inv_id=1)

'''

class RobokassaClient:
    
    def __init__(
        self,
        merchant_login: str,
        password1: str,
        password2: str,
        is_test: bool = True,
        timeout: int = 30,
        logger: list[logging.Logger] = None
    ) -> None:
      pass

# Формирую url
def get_payment_url(
        self,
        merchant_login,
        password1,
        invoice_id: list[int, str],
        amount: list[float, str, Decimal],
        description: str,
        currency: str = "RUB",
        email: list[str] = None,
        culture: str = "ru",
        is_test: bool = True,
        **additional_params,
    ) -> str:

    amount_dec = f"{Decimal(str(amount)):.2f}"

    signature = _calculate_signature(merchant_login, amount_dec, invoice_id, password1)

    all_date={
        'MerchantLogin' : merchant_login,
        'OutSum' : amount_dec,
        'InvId' : invoice_id,
        'Description' : description,
        'SignatureValue':  signature,
#        'Culture' : culture,
#        'Email' : email,
        'IsTest': is_test
    }

    return f'{self.payment_url}?{parse.urlencode(all_date)}'


# Формированаие signature
def _calculate_signature(self, *values: any) -> str:
    string_to_hash = ':'.join(str(arg) for arg in values)
    signature = hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()
    return signature


# Парсим данные из request и помещаем их в dict 
def parse_response(request: str) -> dict:
    params = {}

    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
        for i,k in params.items():
            print(i, ' = ', k)
    return params


# Сравнивает сформированную сигнатуру с полученной от robokassa
def check_signature_result(
    invoice_id: int,  # invoice number
    amount: decimal,  # cost of goods, RU
    received_signature: hex,  # SignatureValue
    password1: str  # Merchant password
) -> bool:
    signature = _calculate_signature(amount, invoice_id, password1)
    if signature.lower() == received_signature.lower():
        return True
    return False


# Получение уведомления об исполнении операции (SuccessURL).
def verify_callback_signature(
    invoice_id: int,  # invoice number
    amount: Decimal,  # cost of goods, RU
    received_signature: hex,  # SignatureValue
    password1: str, # Merchant password
    request
) -> bool:
    
    param_request = parse_response(request)

    amount = param_request['OutSum']
    invoice_id = param_request['InvId']
    signature = param_request['SignatureValue']
    
    if check_signature_result(invoice_id, amount, signature, password1):
        return "Thank you for using our service"
    return "bad sign"


# После сравнения signature формируем ответ для РобоКассы (ResultURL)
def get_payment_status(
    password2: str,  # Merchant password
    request,
) -> bool:
    
    param_request = parse_response(request) # Получаем словарь из parse_response

    amount = param_request['OutSum']
    invoice_id = param_request['InvId']
    signature = param_request['SignatureValue']

    if check_signature_result(invoice_id, amount, signature, password2): # Сравнивааем 
        return f'OK{param_request["InvId"]}'
    return "bad sign"


