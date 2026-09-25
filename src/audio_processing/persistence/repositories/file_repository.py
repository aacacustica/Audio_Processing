from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from audio_processing.persistence.models import ( MeasurementContext)


class FileRepository:

    def __init__(self,session: Session):

        self.session = session


    def list_by_context(self,context_id: int) -> list[SourceFile]:

        statement = (
            select(SourceFile)
            .where(
                SourceFile.id_contexto == context_id
            )
            .order_by(
                SourceFile.datetime_inicio
            )
        )

        return list(self.session.scalars(statement).all())



        