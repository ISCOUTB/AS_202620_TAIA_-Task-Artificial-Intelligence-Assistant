from dataclasses import dataclass, field
from enum import Enum


@dataclass
class IncommingRequest: #Las solicitudes provenientes del usuario
    user_id: str
    text: str
    action: str
