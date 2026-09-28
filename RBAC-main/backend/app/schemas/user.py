from pydantic import BaseModel
from typing import Optional


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    workspace_id: str

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
