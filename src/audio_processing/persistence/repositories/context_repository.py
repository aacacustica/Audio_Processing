from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from audio_processing.persistence.models import Contexto,Campaign,Punto,Device



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


    def get_for_source(self,*,campaign_name:str,point_name:str,device_type:str) -> Contexto:

        statement = (
            select(Contexto)
            .join(Contexto.point)
            .join(Contexto.device)
            .join(Contexto.campaign)
            .options(
                joinedload(Contexto.point),
                joinedload(Contexto.device),
                joinedload(Contexto.campaign)
            )
            .where(
                Campaign.nombre == campaign_name,
                Punto.nombre == point_name,
                Device.tipo == device_type
            )
        )

        contexts = list(self.session.scalars(statement).all())

        if not contexts: raise LookupError(f"No existe contexto para: campaña = {campaign_name},punto = {point_name},dispositivo = {device_type}")
        if len(contexts) > 1: raise LookupError(f"Hay varios contextos para: campaña = {campaign_name},punto = {point_name},dispositivo = {device_type}")

        return contexts[0]

        