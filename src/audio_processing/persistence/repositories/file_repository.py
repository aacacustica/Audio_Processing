from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime


from audio_processing.persistence.models import SourceFile

class FileRepository:

    def __init__(self,session: Session):

        self.session = session


    def list_by_context(self,context_id: int) -> list[SourceFile]:

        statement = (
            select( SourceFile )
            .where( SourceFile.id_contexto == context_id )
            .order_by( SourceFile.datetime_inicio ) 
        )

        return list(self.session.scalars(statement).all())

    def get_by_context_and_filename(self,*,context_id: int,filename: str) -> SourceFile | None:

        statement = (
            select(SourceFile)
            .where(SourceFile.id_contexto == context_id,SourceFile.filename == filename)
        )

        return self.session.scalar(statement)


    def register(self,*,context_id: int, filename: str,datetime_inicio: datetime | None,duracion_seconds: float | None, sample_rate_hz: int | None, file_hash: str | None = None) -> SourceFile:

        source_file = self.get_by_context_and_filename(context_id=context_id,filename=filename)

        if source_file is None:

            source_file = SourceFile(
                id_contexto     = context_id,
                filename        = filename,
                hash            = file_hash,
                datetime_inicio = datetime_inicio,
                duracion_seconds= duracion_seconds,
                sample_rate_hz  = sample_rate_hz,
            )

            self.session.add(source_file)

        else:

            source_file.hash = file_hash
            source_file.datetime_inicio = datetime_inicio
            source_file.duracion_seconds = duracion_seconds
            source_file.sample_rate_hz = sample_rate_hz

        self.session.flush()

        return source_file




        