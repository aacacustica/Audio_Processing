from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime,timezone


from audio_processing.persistence.models import SourceFile,SourceFileProcessing

class FileRepository:

    def __init__(self,session: Session):

        self.session = session

    def is_stage_complete(self,*,file_id: int, stage: str, content_hash: str) -> bool:

        record = self.session.get(SourceFileProcessing,(file_id,stage))
        return record is not None and record.content_hash == content_hash

    def mark_stage_complete(self,*,file_id: int,stage: str, content_hash: str) -> None:

        record = self.session.get(SourceFileProcessing,(file_id,stage))

        if record is None:
            record = SourceFileProcessing(id_archivo=file_id,stage=stage,content_hash=content_hash)
            self.session.add(record)
        else:
            record.content_hash = content_hash
            record.completed_at = datetime.now(timezone.utc)

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

            source_file.hash                = file_hash
            source_file.datetime_inicio     = datetime_inicio
            source_file.duracion_seconds    = duracion_seconds
            source_file.sample_rate_hz      = sample_rate_hz

        self.session.flush()

        return source_file




        