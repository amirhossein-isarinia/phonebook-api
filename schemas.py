from pydantic import BaseModel, field_validator


class ContactCreate(BaseModel):
    name: str
    phone: str
    city: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty")

        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Phone cannot be empty")

        if not value.isdigit():
            raise ValueError("Phone must contain only digits")

        if len(value) < 10 or len(value) > 15:
            raise ValueError("Phone must contain between 10 and 15 digits")

        return value

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("City cannot be empty")

        return value


class ContactUpdate(BaseModel):
    phone: str
    city: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Phone cannot be empty")

        if not value.isdigit():
            raise ValueError("Phone must contain only digits")

        if len(value) < 10 or len(value) > 15:
            raise ValueError("Phone must contain between 10 and 15 digits")

        return value

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("City cannot be empty")

        return value


class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Username cannot be empty")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")

        return value
