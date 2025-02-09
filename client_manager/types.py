from typing import TypedDict


class PersonValues(TypedDict):
    """Person has first and last names"""
    first_name: str
    last_name: str


class ContactValues(PersonValues, total=False):
    """Contact is a person with optional email and phone numbers"""
    email: str
    phone_numbers: list[str]


class ClientValues(ContactValues):
    """Client is a contact with a unique ID"""
    client_id: int


class ClientSearchValues(TypedDict, total=False):
    """Fields to search clients by"""
    first_name: str
    last_name: str
    email: str
    phone_number: str
