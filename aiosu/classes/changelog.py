from datetime import datetime
from .models import BaseModel


class Build(BaseModel):
    id: int
    created_at: datetime
