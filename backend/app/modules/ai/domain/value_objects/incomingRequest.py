from dataclasses import dataclass
from enum import Enum


@dataclass
class IncommingRequest: #Las solicitudes provenientes del usuario
    user_id: str
    text: str

class intent(str, Enum):
    post_task= "Post task"
    read_task= "Read task"
    update_task= "Update task"
    unknown= "Unknown"
