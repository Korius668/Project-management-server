from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., examples=["Unauthorized"])


class MessageResponse(BaseModel):
    message: str


class LoginResponse(BaseModel):
    jwt_token: str
