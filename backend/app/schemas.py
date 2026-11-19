from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

class RegisterIn(BaseModel):
    email: EmailStr
    gamer_tag: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_ -]+$")
    password: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    remember_me: bool = False

class UserOut(BaseModel):
    id: int
    email: EmailStr
    gamer_tag: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CommentIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    email: EmailStr | None = None
    body: str = Field(min_length=1, max_length=3000)

class NewsletterIn(BaseModel):
    email: EmailStr

class ContactIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    topic: str = Field(default="General", max_length=120)
    rank: str | None = Field(default=None, max_length=120)
    message: str = Field(min_length=5, max_length=5000)

class CheckoutIn(BaseModel):
    plan: str = Field(pattern="^(monthly|yearly)$")

class PostOut(BaseModel):
    id: int
    slug: str
    title: str
    excerpt: str
    category: str
    image_path: str | None
    is_premium: bool
    created_at: str

class PostCreateIn(BaseModel):
    slug: str = Field(
        min_length=3,
        max_length=220,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    title: str = Field(min_length=3, max_length=250)
    excerpt: str = Field(default="", max_length=3000)
    body: str = Field(min_length=1)
    category: str = Field(default="Gaming", max_length=80)
    image_path: str | None = None
    is_premium: bool = False
    is_published: bool = True


class PostUpdateIn(PostCreateIn):
    pass
    pass
