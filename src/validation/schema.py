from pydantic import BaseModel, field_validator, ValidationError
from typing import List

class ChestXrayRecord(BaseModel):
    image_index: str
    finding_labels: List[str]
    follow_up_number: int
    patient_id: int
    patient_age: int
    patient_gender: str
    view_position: str
    original_width: int
    original_height: int
    pixel_spacing_x: float
    pixel_spacing_y: float

    @field_validator("patient_age")
    @classmethod
    def age_must_be_reasonable(cls, v):
        if not (0 <= v <= 120):
            raise ValueError(f"Edad fuera de rango: {v}")
        return v

    @field_validator("patient_gender")
    @classmethod
    def gender_must_be_valid(cls, v):
        if v not in ("M", "F"):
            raise ValueError(f"Género inválido: {v}")
        return v

    @field_validator("view_position")
    @classmethod
    def view_must_be_valid(cls, v):
        if v not in ("AP", "PA"):
            raise ValueError(f"Posición de vista inválida: {v}")
        return v

    @field_validator("original_width", "original_height")
    @classmethod
    def dimensions_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError(f"Dimensión inválida: {v}")
        return v

    @field_validator("pixel_spacing_x", "pixel_spacing_y")
    @classmethod
    def spacing_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError(f"Pixel spacing inválido: {v}")
        return v