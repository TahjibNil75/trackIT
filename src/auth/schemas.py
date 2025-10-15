import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from src.errors import PasswordMismatchError


class UserCreateModel(BaseModel):
    username : str = Field(
        ...,
        min_length=2,
        description="The username of the user. Must be unique.",
        example="john_doe75"
    )
    email : str = Field(
        ...,
        min_length=5,
        max_length=50,
        description="The email of the user. Must be unique.",
    )
    full_name : Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="The full name of the user.",
        example="John Doe"
    )
    password : str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="The password of the user. Must be at least 8 characters long.",
        example="strongpassword123"
    )
    password_confirm : str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password confirmation. Must match the password.",
        example="strongpassword123"
    )
    @field_validator("password_confirm")
    def passwords_match(cls, v,info: ValidationInfo):
        password = info.data.get("password")
        if password != v:
            raise PasswordMismatchError()
        return v



class UserResponseModel(BaseModel):
    user_id : uuid.UUID
    username : str
    email : str
    full_name : Optional[str]
    role : str
    created_at : datetime
    updated_at : datetime

class UserLoginModel(BaseModel):
    username : str = Field(
        ...,
        min_length=2,
        example="john_doe75"
    )
    email : str = Field(
        ...,
        min_length=5,
        max_length=50,
    )
    password : str = Field(
        ...,
        min_length=8,
        max_length=128,
        example="strongpassword123"
    )
