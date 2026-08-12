from datetime import date
from pydantic import BaseModel


class TipoHurto(BaseModel):
    nombre: str


class Hurto(BaseModel):
    idtipohurto: int
    denunciante: str
    direccion: str
    fechahurto: date