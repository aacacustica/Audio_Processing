from datetime import datetime, timezone

from sqlalchemy import select

from audio_processing.campaign.config import load_config
from audio_processing.persistence.database import Database
from audio_processing.persistence.models import (
    Punto,
    Device,
    Campaign,
    Contexto,
    SourceFile,
)


def main():

    config = load_config()
    db = Database.from_config(config)

    with db.session() as session:

        # Evita ejecutar el seed dos veces
        existing_context = session.scalar(
            select(Contexto)
            .where(Contexto.id_contexto == 1)
            
        )

        if existing_context is not None:
            print("El contexto 1 ya existe.")
            return

        point = Punto(
            nombre      = "P3 - test",
            municipio   = "Vitoria-Gasteiz",
            latitud     = None,
            longitud    = None,
        )

        device = Device(
            nombre                  = "Audiomoth test",
            requiere_calibracion    = True,
            valor_calibracion       = -10.16,
            fecha_calibracion       = None,
        )

        campaign = Campaign(
            nombre                  = "CAMPAÑA TEST ACLIMA",
            referencia_interna      = "ACLIMA_TEST",
            fecha_inicio            = datetime(2926,9,28,tzingo=timezone.utc),
            fecha_fin               = None,
            descripcion             = "Campaña de prueba para desarrollo.",
        )

        session.add_all([ point , device , campaign ])

        session.flush()

        context = Contexto(
            id_punto                = point.id_punto,
            id_dispositivo          = device.id_dispositivo,
            id_campania             = campaign.id_campania,
            altura                  = 4.0,
            soporte                 = "Farola",
            fecha_inicio            = datetime(2026,9,28,8,0,tzinfo=timezone.utc),
            fecha_fin               = None,
        )

        session.add(context)
        session.flush()

        source_file = SourceFile(
            id_contexto             = context.id_contexto,
            filename                = "20260928_080000.WAV",
            hash                    = None,
            datetime_inicio         = datetime(2026,9,28,8,0,tzinfo=timezone.utc),
            duracion_seconds        = 60.0,
            sample_rate_hz          = 48000,
        )

        session.add(source_file)

        print("Datos de prueba creados.")


if __name__ == "__main__":
    main()