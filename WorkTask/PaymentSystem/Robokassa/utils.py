import hashlib
from decimal import Decimal
from exceptions import ValidationError
from models import HashAlgorithm

def calculate_signature(merchant_login: str, amount, invoice_id, password: str, algorithm: HashAlgorithm = HashAlgorithm.MD5) -> str:
    data_str = f"{merchant_login}:{amount}:{invoice_id}:{password}"
    if algorithm == HashAlgorithm.MD5:
        return hashlib.md5(data_str.encode()).hexdigest()
    elif algorithm == HashAlgorithm.SHA256:
        return hashlib.sha256(data_str.encode()).hexdigest()
    else:
        raise ValidationError(f"Неизвестный алгоритм подписи: {algorithm}")
    
def validate_payment_parameters(invoice_id, amount, description):
    if not invoice_id:
        raise ValidationError("invoice_id is required")
    if not amount or Decimal(amount) <= 0:
        raise ValidationError("amount must be > 0")
    if not description:
        raise ValidationError("description is required")