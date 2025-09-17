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
API_STATUS_URL = ''

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
        self.merchant_login = merchant_login
        self.password1 = password1
        self.password2 = password2
        self.is_test = is_test
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)

    # Формирую url
    def get_payment_url(
            self,
            invoice_id: list[int, str],
            amount: list[float, str, Decimal],
            description: str,
            currency: str = "RUB",
            email: list[str] = None,
            culture: str = "ru",
            is_test: bool = True,
            **additional_params,
        ) -> str:
                    
            validate_payment_parameters(invoice_id, amount, description)
    
            signature = _calculate_signature_arg(
                self.merchant_login, amount, invoice_id, self.password1)
    
            all_date={
            'MerchantLogin' : self.merchant_login,
            'OutSum' : amount,
            'InvId' : invoice_id,
            'Description' : description,
            'SignatureValue':  signature,
            'Culture' : culture,
    #        'Email' : email,
        }
            if email:
                all_date['Email'] = email
    
            return f'{self.payment_url}?{parse.urlencode(all_date)}'
    
    
    # Формированаие signature
    def _calculate_signature(self, *values: any) -> str:
        string_to_hash = ':'.join(str(arg) for arg in values)
        signature = hashlib.md5(string_to_hash.encode('utf-8')).hexdigest()
        return signature
    
# Возвращаем статус по InvoiceId
    def get_payment_status_args(
            self,
            invoice_id: Union[int, str],
            amount: Optional[Union[float, str, Decimal]] = None
        ) -> PaymentStatus:
            try:
                response = requests.get(API_STATUS_URL,
                                        params={
                        'InvoiceId' : invoice_id
                                        })
                response.raise_for_status()
                date = response.json()
                status = date.get('InvoiceStatuses')
                if status.lower() == 'paid':
                    return PaymentStatus.PAID
                else:
                     return PaymentStatus.CREATED
            except Exception as e:
                return 'Error'
    
    # Список платежей по параметрам
    def get_payments_list(self,
                        date_from: datetime,
                        date_to: datetime, 
                        status: Optional[PaymentStatus] = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Payment]:
            try:
                resp = requests.get(
                    API_STATUS_URL,
                        params={
                            "DateFrom": date_from,
                            "DateTo": date_to,
                            "Status": status,
                            "Limit": limit,
                            "Offset": offset
                            },
                        timeout=self.timeout,
                )
    
                resp.raise_for_status()
                data = resp.json()
                return [Payment(**payment) for payment in data]
            except Exception as e:
                raise APIError(f"Failed to get payments list: {e}")



