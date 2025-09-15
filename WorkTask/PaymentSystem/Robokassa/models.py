from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict

class PaymentStatus(Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    

class HashAlgorithm(Enum):
    MD5 = "MD5"
    SHA256 = "SHA256"
    

@dataclass
class Payment:
    invoice_id: int
    amount: Decimal
    currency: str
    description: str
    status: PaymentStatus
    created_at: datetime
    updated_at: [Optional[datetime]] = None
    email: [Optional[str]] = None
    custom_parameters: [Optional[Dict[str, str]]] = None