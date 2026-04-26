from pydantic import BaseModel, model_validator


class RequestOTPInput(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None

    @model_validator(mode="after")
    def require_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("At least one of email or phone is required")
        return self


class VerifyOTPInput(BaseModel):
    email: str | None = None
    phone: str | None = None
    code: str

    @model_validator(mode="after")
    def require_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("At least one of email or phone is required")
        return self


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str | None
    phone: str | None
