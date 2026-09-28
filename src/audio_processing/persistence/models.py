from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean,DateTime,Float,ForeignKey,Integer,String,Index,UniqueConstraint
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship


class Base(DeclarativeBase):
    pass


class Device(Base):

    __tablename__ = "dispositivo"

    id_dispositivo:             Mapped[int]             = mapped_column(Integer,primary_key=True)
    nombre:                     Mapped[str]             = mapped_column(String(256),nullable=False)
    requiere_calibracion:       Mapped[bool]            = mapped_column(Boolean,nullable=False,default=False)
    valor_calibracion:          Mapped[float | None]    = mapped_column(Float)
    fecha_calibracion:          Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Campaign(Base):

    __tablename__ = "campania"

    id_campania:                Mapped[int]             = mapped_column(Integer,primary_key=True)
    nombre:                     Mapped[str]             = mapped_column(String(255),nullable=False)
    referencia_interna:         Mapped[str]             = mapped_column(String(255),nullable=False)
    fecha_inicio:               Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin:                  Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    descripcion:                Mapped[str | None]      = mapped_column(String)

class Punto(Base):

    __tablename__ = "punto"

    id_punto:                   Mapped[int]             = mapped_column(Integer,primary_key=True)
    nombre:                     Mapped[str]             = mapped_column(String(255),nullable=False)
    municipio:                  Mapped[str]             = mapped_column(String(255),nullable=False)
    latitud:                    Mapped[float | None]    = mapped_column(Float)
    longitud:                   Mapped[float | None]    = mapped_column(Float)

class Contexto(Base):

    __tablename__ = "contexto"

    __table_args__ = ( Index("ix_contexto_punto_campania_dispositivo","id_punto","id_campania","id_dispositivo"),)

    id_contexto:                Mapped[int]             = mapped_column(Integer,primary_key=True)

    id_punto:                   Mapped[int]             = mapped_column(ForeignKey("punto.id_punto"),nullable=False)
    id_dispositivo:             Mapped[int]             = mapped_column(ForeignKey("dispositivo.id_dispositivo"),nullable=False)
    id_campania:                Mapped[int]             = mapped_column(ForeignKey("campania.id_campania"),nullable=False)

    altura:                     Mapped[float | None]    = mapped_column(Float)
    soporte:                    Mapped[str | None]      = mapped_column(String(255))
    fecha_inicio:               Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fecha_fin:                  Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    point:                      Mapped[Punto]           = relationship()
    device:                     Mapped[Device]          = relationship()
    campaign:                   Mapped[Campaign]        = relationship()


class SourceFile(Base):

    __tablename__ = "archivo"

    __table_args__ = (UniqueConstraint("id_contexto","filename",name="uq_archivo_contexto_filename"),)

    id_archivo:             Mapped[int]                 = mapped_column(Integer,primary_key=True)

    id_contexto:            Mapped[int]                 = mapped_column(ForeignKey("contexto.id_contexto"),nullable=False)

    filename:               Mapped[str]                 = mapped_column(String(1024),nullable=False)
    hash:                   Mapped[str | None]          = mapped_column(String(1024))
    duracion_seconds:       Mapped[float | None]        = mapped_column(Float)
    datetime_inicio:        Mapped[datetime | None]     = mapped_column(DateTime(timezone=True))
    sample_rate_hz:         Mapped[int | None]          = mapped_column(Integer)


class AcousticMeasurement(Base):

    __tablename__ = "medicion_acustica"

    id_medicion:            Mapped[int]                 = mapped_column(Integer,primary_key=True)

    id_contexto:            Mapped[int]                 = mapped_column(ForeignKey("contexto.id_contexto"),nullable=False,index=True)
    id_archivo:             Mapped[int | None]          = mapped_column(ForeignKey("archivo.id_archivo"),nullable=True,index=True)

    datetime:               Mapped[datetime]            = mapped_column(DateTime(timezone=True),nullable=False,index=True)
    aggregation_seconds:    Mapped[float]               = mapped_column(Float,nullable=False)

    la_db:                  Mapped[float | None]        = mapped_column(Float)
    lc_db:                  Mapped[float | None]        = mapped_column(Float)
    lz_db:                  Mapped[float | None]        = mapped_column(Float)
    la_max_db:              Mapped[float | None]        = mapped_column(Float)
    la_min_db:              Mapped[float | None]        = mapped_column(Float)
    lc_la_db:               Mapped[float | None]        = mapped_column(Float)
