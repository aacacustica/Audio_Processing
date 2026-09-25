from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from audio_processing.persistence.models import ( MeasurementContext)



class ContextRepository:

    def __init__(self,session: Session):

        self.session = session

    def get(self,context_id:int) -> MeasurementContext | None:

        statement = (
            select(MeasurementContext).options(
                joinedload(MeasurementContext.point),
                joinedload(MeasurementContext.device),
                joinedload(MeasurementContext.campaign)

                ).where(
                    MeasurementContext.id_contexto == context_id
                )
        )

        return self.session.scalar(statement)


    def get_required(self,context_id:int) -> MeasurementContext:

        context = self.get(context_id)

        if context is None: raise LookupError(f"No existe contexto {context_id}")

        return context