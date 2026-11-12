from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ClientRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    company_name: str | None = Field(default=None, max_length=180)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str
    country: str = Field(min_length=2, max_length=100)
    terms_accepted: bool


class FreelancerRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str
    country: str = Field(min_length=2, max_length=100)
    professional_title: str = Field(min_length=2, max_length=180)
    skills: list[str] = Field(min_length=1, max_length=30)
    experience_years: int = Field(ge=0, le=60)
    terms_accepted: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    country: str

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse