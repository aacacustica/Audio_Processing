from audio_processing.campaign.config import load_config

from audio_processing.persistence.database import Database

from audio_processing.persistence.repositories.context_repository import (
    ContextRepository
)

from audio_processing.persistence.repositories.file_repository import (
    FileRepository
)


def main():

    config = load_config(
        
    )

    db = Database.from_config(
        config
    )

    with db.session() as session:

        context_repo = ContextRepository(
            session
        )

        file_repo = FileRepository(
            session
        )

        context = context_repo.get_required(
            1
        )

        files = file_repo.list_by_context(
            context.id_contexto
        )

        print(
            "Punto:",
            context.point.nombre
        )

        print(
            "Dispositivo:",
            context.device.nombre
        )

        print(
            "Campaña:",
            context.campaign.nombre
        )

        print()
        print("Archivos:")

        for file in files:
            print(
                "-",
                file.filename
            )


if __name__ == "__main__":
    main()