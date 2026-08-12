from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AddressBase(BaseModel):
    label: str = Field(default="Rumah", max_length=50)
    recipient_name: str = Field(..., max_length=255)
    phone: str = Field(..., max_length=20)
    address_line: str = Field(..., max_length=500)
    kelurahan: Optional[str] = Field(None, max_length=100)
    kecamatan: Optional[str] = Field(None, max_length=100)
    kota: str = Field(..., max_length=100)
    provinsi: str = Field(..., max_length=100)
    kode_pos: Optional[str] = Field(None, max_length=10)
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=50)
    recipient_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address_line: Optional[str] = Field(None, max_length=500)
    kelurahan: Optional[str] = Field(None, max_length=100)
    kecamatan: Optional[str] = Field(None, max_length=100)
    kota: Optional[str] = Field(None, max_length=100)
    provinsi: Optional[str] = Field(None, max_length=100)
    kode_pos: Optional[str] = Field(None, max_length=10)
    is_default: Optional[bool] = None


class Address(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime