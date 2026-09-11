from pydantic import BaseModel
from uuid import UUID
from datetime import datetime



class Notification(BaseModel):
    reminder_id: int
    message: str
    read_status: bool = False  
    date_send: datetime   

    def send_notification(self):
        return Notification.message
        #paso a caso de uso

