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
    def from_dict(cls, data: Dict[str, Any]) -> 'Conflict':
        """Create Conflict from dictionary"""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if v is not None
        }


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
    def from_dict(cls, data: Dict[str, Any]) -> 'ConflictNote':
        """Create ConflictNote from dictionary"""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if v is not None
        }