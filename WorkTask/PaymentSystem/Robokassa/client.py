import logging
import requests
from decimal import Decimal
from typing import Any, Dict, Optional, Union
from constants import BASE_URL, API_STATUS_URL, DEFAULT_TIMEOUT
from exceptions import APIError
from models import Payment, PaymentStatus, HashAlgorithm
from utils import calculate_signature, validate_payment_parameters

class RobokassaClient:
    def __init__(
        self,
        merchant_login: str,
        password1: str,
        password2: str,
        is_test: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        logger: Optional[logging.Logger] = None,
        algorithm: HashAlgorithm = HashAlgorithm.MD5,
    ):
        self.merchant_login = merchant_login
        self.password1 = password1
        self.password2 = password2
        self.is_test = is_test
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        self.algorithm = algorithm

    def get_payment_url(
        self,
        invoice_id: Union[int, str],
        amount: Union[float, str, Decimal],
        description: str,
        currency: str = "RUB",
        email: Optional[str] = None,
        culture: str = "ru",
        **kwargs: Any
    ) -> str:
        validate_payment_parameters(invoice_id, amount, description)
        signature = calculate_signature(
            self.merchant_login,
            amount,
            invoice_id,
            self.password1,
            algorithm=self.algorithm
        )
        params = {
            "MerchantLogin": self.merchant_login,
            "OutSum": amount,
            "InvId": invoice_id,
            "Description": description,
            "SignatureValue": signature,
            "Culture": culture,
            "Encoding": "utf-8",
        }
        if email:
            params["Email"] = email
        return f"{BASE_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    def verify_callback_signature(self, request_params: Dict[str, Any], is_result_url: bool = True) -> bool:
        if is_result_url:
            values = [
                request_params.get("OutSum"),
                request_params.get("InvId"),
                self.password2,
            ]
        else:
            values = [
                request_params.get("OutSum"),
                request_params.get("InvId"),
                self.password1,
            ]
        expected_signature = calculate_signature(*values, algorithm=self.algorithm).lower()
        return expected_signature == request_params.get("SignatureValue", "").lower()

    def get_payment_status(self, invoice_id: Union[int, str]) -> PaymentStatus:
        try:
            resp = requests.get(
                API_STATUS_URL,
                params={"InvoiceId": invoice_id},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return PaymentStatus.PAID if data.get("IsPaid") else PaymentStatus.CREATED
        except Exception as e:
            raise APIError(f"Failed to get status: {e}")
