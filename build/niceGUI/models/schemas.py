# /build/niceGUI/models/schemas.py

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime

# Pydantic models provide runtime type validation, which is more robust
# than standard dataclasses for this use case.

# =================== Usuarios y Roles ===================


class RoleBase(BaseModel):
    nombre: str = Field(..., max_length=50)
    descripcion: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True


class UsuarioBase(BaseModel):
    alias: str = Field(..., max_length=50)
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None


class UsuarioCreate(UsuarioBase):
    password: str  # Include password only for creation


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class Usuario(UsuarioBase):
    id: int
    is_active: bool
    created_at: datetime
    roles: List[Role] = []

    class Config:
        from_attributes = True


# =================== Estructura Inmobiliaria ===================


class EntramadoEmpresaBase(BaseModel):
    nombre: str = Field(..., max_length=255)
    descripcion: Optional[str] = None


class EntramadoEmpresaCreate(EntramadoEmpresaBase):
    pass


class EntramadoEmpresa(EntramadoEmpresaBase):
    id: int

    class Config:
        from_attributes = True


class EmpresaBase(BaseModel):
    nombre: str
    cif_nif_nie: Optional[str] = Field(None, max_length=20)
    entramado_id: Optional[int] = None


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(BaseModel):
    nombre: Optional[str] = None
    cif_nif_nie: Optional[str] = Field(None, max_length=20)
    entramado_id: Optional[int] = None


class Empresa(EmpresaBase):
    id: int

    class Config:
        from_attributes = True


class BloqueBase(BaseModel):
    direccion: str
    estado: Optional[str] = None
    empresa_id: Optional[int] = None
    nodo_id: Optional[int] = None


class BloqueCreate(BloqueBase):
    pass


class BloqueUpdate(BaseModel):
    direccion: Optional[str] = None
    estado: Optional[str] = None
    empresa_id: Optional[int] = None
    nodo_id: Optional[int] = None


class Bloque(BloqueBase):
    id: int

    class Config:
        from_attributes = True


class PisoBase(BaseModel):
    direccion: str
    municipio: Optional[str] = None
    cp: Optional[int] = None
    bloque_id: Optional[int] = None


class PisoCreate(PisoBase):
    pass


class PisoUpdate(BaseModel):
    direccion: Optional[str] = None
    municipio: Optional[str] = None
    cp: Optional[int] = None
    bloque_id: Optional[int] = None


class Piso(PisoBase):
    id: int

    class Config:
        from_attributes = True


# =================== Afiliadas y Conflictos ===================


class AfiliadaBase(BaseModel):
    num_afiliada: str = Field(..., max_length=50)
    nombre: str
    apellidos: str
    piso_id: Optional[int] = None


class AfiliadaCreate(AfiliadaBase):
    pass


class AfiliadaUpdate(BaseModel):
    num_afiliada: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    piso_id: Optional[int] = None
    estado: Optional[str] = None


class Afiliada(AfiliadaBase):
    id: int
    estado: Optional[str] = None
    fecha_alta: Optional[date] = None

    class Config:
        from_attributes = True


class ConflictoBase(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = Field("Abierto", max_length=50)
    causa: Optional[str] = None
    fecha_apertura: date
    afiliada_id: int
    usuario_responsable_id: Optional[int] = None


class ConflictoCreate(ConflictoBase):
    pass


class ConflictoUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = Field(None, max_length=50)
    causa: Optional[str] = None
    fecha_cierre: Optional[date] = None
    usuario_responsable_id: Optional[int] = None


class Conflicto(ConflictoBase):
    id: int
    fecha_cierre: Optional[date] = None

    class Config:
        from_attributes = True


from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Conflict:
    """Conflict data model"""

    id: int
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    causa: Optional[str] = None
    ambito: Optional[str] = None
    fecha_apertura: Optional[str] = None
    fecha_cierre: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conflict":
        """Create Conflict from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ConflictNote:
    """Conflict note/history entry"""

    id: Optional[int] = None
    conflicto_id: Optional[int] = None
    accion_id: Optional[int] = None
    usuario_id: Optional[int] = None
    estado: Optional[str] = None
    ambito: Optional[str] = None
    notas: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConflictNote":
        """Create ConflictNote from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in self.__dict__.items() if v is not None}
