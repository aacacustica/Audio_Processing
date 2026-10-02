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
    tipo:                       Mapped[str]             = mapped_column(String(64),nullable=False,index=True)
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

    __table_args__ = (UniqueConstraint("id_archivo","datetime","aggregation_seconds",name="uq_medicion_archivo_datetime_aggregation"),)

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

class AcousticThirdOctaveMeasurements(Base):

    __tablename__ = "medicion_acustica_en_tercios"

    id_medicion:            Mapped[int]                 = mapped_column(ForeignKey("medicion_acustica.id_medicion",ondelete="CASCADE",),primary_key=True)

    band_12_5_db:           Mapped[float | None]        = mapped_column(Float)
    band_16_db:             Mapped[float | None]        = mapped_column(Float)
    band_20_db:             Mapped[float | None]        = mapped_column(Float)
    band_25_db:             Mapped[float | None]        = mapped_column(Float)
    band_31_5_db:           Mapped[float | None]        = mapped_column(Float)
    band_40_db:             Mapped[float | None]        = mapped_column(Float)
    band_50_db:             Mapped[float | None]        = mapped_column(Float)
    band_63_db:             Mapped[float | None]        = mapped_column(Float)
    band_80_db:             Mapped[float | None]        = mapped_column(Float)
    band_100_db:            Mapped[float | None]        = mapped_column(Float)
    band_125_db:            Mapped[float | None]        = mapped_column(Float)
    band_160_db:            Mapped[float | None]        = mapped_column(Float)
    band_200_db:            Mapped[float | None]        = mapped_column(Float)
    band_250_db:            Mapped[float | None]        = mapped_column(Float)
    band_315_db:            Mapped[float | None]        = mapped_column(Float)
    band_400_db:            Mapped[float | None]        = mapped_column(Float)
    band_500_db:            Mapped[float | None]        = mapped_column(Float)
    band_630_db:            Mapped[float | None]        = mapped_column(Float)
    band_800_db:            Mapped[float | None]        = mapped_column(Float)
    band_1000_db:           Mapped[float | None]        = mapped_column(Float)
    band_1250_db:           Mapped[float | None]        = mapped_column(Float)
    band_1600_db:           Mapped[float | None]        = mapped_column(Float)
    band_2000_db:           Mapped[float | None]        = mapped_column(Float)
    band_2500_db:           Mapped[float | None]        = mapped_column(Float)
    band_3150_db:           Mapped[float | None]        = mapped_column(Float)
    band_4000_db:           Mapped[float | None]        = mapped_column(Float)
    band_5000_db:           Mapped[float | None]        = mapped_column(Float)
    band_6300_db:           Mapped[float | None]        = mapped_column(Float)
    band_8000_db:           Mapped[float | None]        = mapped_column(Float)
    band_10000_db:          Mapped[float | None]        = mapped_column(Float)
    band_12500_db:          Mapped[float | None]        = mapped_column(Float)
    band_16000_db:          Mapped[float | None]        = mapped_column(Float)
    band_20000_db:          Mapped[float | None]        = mapped_column(Float)


class AIPrediction(Base):

    __tablename__ = "prediccion_ia"

    __table_args__ = (UniqueConstraint("id_archivo","datetime_inicio","window_seconds","class_name","model_name",name="uq_prediccion_archivo_ventana_clase_modelo"),)

    id_prediccion:          Mapped[int]                 = mapped_column(Integer,primary_key=True)
    id_archivo:             Mapped[int]                 = mapped_column(ForeignKey("archivo.id_archivo",ondelete="CASCADE"),nullable=False,index=True)
    datetime_inicio:        Mapped[datetime]            = mapped_column(DateTime(timezone=True),nullable=False,index=True)
    window_seconds:         Mapped[float]               = mapped_column(Float,nullable=False)
    class_name:             Mapped[str]                 = mapped_column(String(255),nullable=False)
    probability:            Mapped[float]               = mapped_column(Float,nullable=False)
    model_name:             Mapped[str]                 = mapped_column(String(128),nullable=False)
    threshold:              Mapped[float]               = mapped_column(Float,nullable=False)
    prediction_rank:        Mapped[int]                 = mapped_column(Integer,nullable=False)


class AIPredictionMeasurement(Base):

    __tablename__ = "prediccion_ia_medicion"

    id_prediccion:          Mapped[int]                 = mapped_column(ForeignKey("prediccion_ia.id_prediccion",ondelete="CASCADE"),primary_key=True)
    id_medicion:            Mapped[int]                 = mapped_column(ForeignKey("medicion_acustica.id_medicion",ondelete="CASCADE"),primary_key=True,index=True)


class AcousticPeak(Base):

    __tablename__ = "pico_acustico"

    __table_args__ = (UniqueConstraint("id_medicion_pico",name="uq_pico_medicion_pico"),)

    id_pico:                Mapped[int]                 = mapped_column(Integer,primary_key=True)
    id_contexto:            Mapped[int]                 = mapped_column(ForeignKey("contexto.id_contexto",ondelete="CASCADE"))
    id_archivo_pico:        Mapped[int | None]          = mapped_column(ForeignKey("archivo.id_archivo",ondelete="SET NULL"),nullable=True,index=True)
    id_medicion_pico:       Mapped[int]                 = mapped_column(ForeignKey("medicion_acustica.id_medicion",ondelete="CASCADE"),nullable=False,index=True)

    datetime_pico:          Mapped[datetime]            = mapped_column(DateTime(timezone=True),nullable=False,index=True)
    start_time:             Mapped[datetime]            = mapped_column(DateTime(timezone=True),nullable=False)
    end_time:               Mapped[datetime]            = mapped_column(DateTime(timezone=True),nullable=False)
    duration_seconds:       Mapped[float]               = mapped_column(Float,nullable=False)
    peak_la_db:             Mapped[float]               = mapped_column(Float,nullable=False)
    leq_db:                 Mapped[float]               = mapped_column(Float,nullable=False)
    prominence_db:          Mapped[float]               = mapped_column(Float,nullable=False)


class AcousticPeakMeasurement(Base):

    __tablename__ = "pico_acustico_medicion"

    id_pico:                Mapped[int]                 = mapped_column(ForeignKey("pico_acustico.id_pico",ondelete="CASCADE"),primary_key=True)
    id_medicion:            Mapped[int]                 = mapped_column(ForeignKey("medicion_acustica.id_medicion",ondelete="CASCADE"),primary_key=True,index=True)
