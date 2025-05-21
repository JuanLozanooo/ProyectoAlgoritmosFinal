from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Integer, Sequence
from fastapi import Form

class CardioHealth(SQLModel, table=True):
    id: Optional[int] = Field(
        sa_column=Column(
            Integer,
            Sequence('cardiohealth_id_seq'),
            primary_key=True,
            autoincrement=True
        ),
        default=None
    )

    age: int = Field(..., ge=1, le=150, description="Edad en años")
    gender: int = Field(..., ge=0, le=1, description="0: Mujer, 1: Hombre")
    height: float = Field(..., ge=0, le=3, description="Altura en metros")
    weight: float = Field(..., ge=20, le=300, description="Peso en kg")
    ap_hi: int = Field(..., ge=50, le=300, description="Presión sistólica")
    ap_lo: int = Field(..., ge=30, le=200, description="Presión diastólica")
    cholesterol: int = Field(..., ge=1, le=3, description="1: Normal, 2: Alto, 3: Muy alto")
    gluc: int = Field(..., ge=1, le=3, description="1: Normal, 2: Alto, 3: Muy alto")
    smoke: int = Field(..., ge=0, le=1, description="0: No fuma, 1: Sí fuma")
    alco: int = Field(..., ge=0, le=1, description="0: No consume alcohol, 1: Sí consume")
    active: int = Field(..., ge=0, le=1, description="0: Inactivo físicamente, 1: Activo físicamente")
    cardio: int = Field(..., ge=0, le=1, description="0: No tiene antecedentes de enfermedad cardiovascular en la familia, 1: Sí tiene")

class CardioHealthCreate(SQLModel):
    @classmethod
    def as_form(
        cls,
        age: int = Form(...),
        gender: int = Form(...),
        height: float = Form(...),
        weight: float = Form(...),
        ap_hi: int = Form(...),
        ap_lo: int = Form(...),
        cholesterol: int = Form(...),
        gluc: int = Form(...),
        smoke: int = Form(default=0),
        alco: int = Form(default=0),
        active: int = Form(default=0),
        cardio: int = Form(default=0)
    ):
        return cls(
            age=age * 365,  # Convertir años a días
            gender=gender,
            height=height * 100,  # Convertir metros a centímetros
            weight=weight,
            ap_hi=ap_hi,
            ap_lo=ap_lo,
            cholesterol=cholesterol,
            gluc=gluc,
            smoke=smoke,
            alco=alco,
            active=active,
            cardio=cardio
        )

class CardioHealthUpdate(SQLModel):
    age: Optional[int] = Field(None, ge=1, le=150, description="Edad en años")
    gender: Optional[int] = Field(None, ge=0, le=1, description="0: Mujer, 1: Hombre")
    height: Optional[float] = Field(None, ge=0, le=3, description="Altura en metros")
    weight: Optional[float] = Field(None, ge=20, le=300, description="Peso en kg")
    ap_hi: Optional[int] = Field(None, ge=50, le=300, description="Presión sistólica")
    ap_lo: Optional[int] = Field(None, ge=30, le=200, description="Presión diastólica")
    cholesterol: Optional[int] = Field(None, ge=1, le=3, description="1: Normal, 2: Alto, 3: Muy alto")
    gluc: Optional[int] = Field(None, ge=1, le=3, description="1: Normal, 2: Alto, 3: Muy alto")
    smoke: Optional[int] = Field(None, ge=0, le=1, description="0: No fuma, 1: Sí fuma")
    alco: Optional[int] = Field(None, ge=0, le=1, description="0: No consume alcohol, 1: Sí consume")
    active: Optional[int] = Field(None, ge=0, le=1, description="0: Inactivo físicamente, 1: Activo físicamente")
    cardio: Optional[int] = Field(None, ge=0, le=1, description="0: No tiene antecedentes, 1: Sí tiene")

class CardioHealthResponse(SQLModel):
    age: int
    gender: int
    height: float
    weight: float
    ap_hi: int
    ap_lo: int
    cholesterol: int
    gluc: int
    smoke: int
    alco: int
    active: int
    cardio: int