from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from entities.notification import Notification
class Reminder(BaseModel):
    id: int
    user_id: UUID
    message: str
    scheduled_at: datetime
    is_active: bool   # cambiar nombre de esta variable a otra mas acorde a un si o no
    task_id: int   # asumiendo que el id de las tareas es por enteros

    def create_notification(self) -> Notification:
        return Notification(
            reminder_id = self.id,
            message = self.message,
            read_status = False,
            date_send = datetime.now() ) # mover a caso de uso
        
        

