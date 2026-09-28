from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from audio_processing.persistence.models import Contexto



class ContextRepository:

    def __init__(self,session: Session):

        self.session = session

    def get(self,context_id:int) -> Contexto | None:

        statement = (
            select(Contexto).options(
                joinedload(Contexto.point),
                joinedload(Contexto.device),
                joinedload(Contexto.campaign)

                ).where(
                    Contexto.id_contexto == context_id
                )
        )

        return self.session.scalar(statement)


    def get_required(self,context_id:int) -> Contexto:

        context = self.get(context_id)

        if context is None: raise LookupError(f"No existe contexto {context_id}")

        return context