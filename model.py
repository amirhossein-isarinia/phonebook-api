from sqlalchemy import Column, Integer, String

from database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String,
        nullable=False
    )

    phone = Column(
        String,
        nullable=False
    )

    city = Column(
        String,
        nullable=False
    )
