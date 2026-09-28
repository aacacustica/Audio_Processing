from __future__ import annotations

from contextlib import contextmanager
import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


DEFAULT_DATABASE_URL_ENV = "AUDIO_PROCESSING_DATABASE_URL"

DEFAULT_DATABASE_URL_ENV = "AUDIO_PROCESSING_DATABASE_URL"

class Database:

    def __init__(self,url:str,*,echo:bool = False):

        if not url: raise ValueError("El campo URL de la base de datos no puede estar vacío.")
            

        self.engine = create_engine(url=url,echo=echo,pool_pre_ping=True)

        self._session_factory = sessionmaker(bind=self.engine,class_=Session,expire_on_commit=False)


    @classmethod
    def from_config(cls,config) -> "Database":

        db_config = getattr(config,"database",None)

        if db_config is None: raise ValueError("Falta database en la configuración.")

        url = getattr(db_config,"url",None)

        if not url: 
            env_name = getattr(db_config,'url_env',DEFAULT_DATABASE_URL_ENV)
            url = os.getenv(env_name)
        else:
            env_name = ""
        if not url: raise ValueError("No se ha configurado la URL de la base de datos.")

        print("ENV NAME:", repr(env_name))
        print("DATABASE URL:", repr(url))
        print("TYPE URL:", type(url))
        return cls(url=url,echo=getattr(db_config,"echo",False))

    @classmethod 
    def create_table_punto():

        None

    @classmethod
    def create_table_dispositivo():

        None

    @classmethod
    def create_table_campaña():

        None

    
    


    @contextmanager
    def session(self) -> Generator[Session]:

        session = self._session_factory()

        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally: 
            session.close()


    


