# FastAPI Project

This project consists of creating and communicating an API and a Database for structuring and visualizing data obtained from audio processing.

## Project Structure

There are two main folders:

### 1. `fast_api/prueba`

This folder contains tests for understanding the FASTAPI framework and the SQLAlchemy database tool.

- `structure.txt`: Describes the structure of the Database to be developed in SQLAlchemy.
- `main.py`: Defines the FastAPI application, configures middleware, and includes routers (API endpoints). Routers are usually distributed in different files and included in the main application using `app.include_router()`. This file also manages database sessions, handling the opening and closing of sessions for each request.
- `models.py`: Defines SQLAlchemy models. These are classes mapped to database tables. They inherit from the `Base` class defined in `database.py`, and each model attribute represents a table column. These models are used to create, retrieve, update, and delete records in the database.
- `schemas.py`: Defines Pydantic models (schemas) for parsing and validating JSON data sent and received by the API. These schemas are used by FastAPI to automatically generate API documents and validate incoming request data.
- `crud.py`: Stands for Create, Read, Update, Delete. This file contains functions for interacting with the database using models defined in `models.py`.

### 2. `fast_api/api_db`

This folder contains the developed API and Database. It includes the same files as the previous folder plus:

- `database.py`: Configures the SQLAlchemy database engine and sessionmaker. Contains all details to connect to the specific database. The engine and `SessionLocal` created here are used throughout the application to interact with the database.
- An audio file: Used for testing communication. Once the tools are deployed, communication is verified by creating an endpoint that stores an audio file locally when it is uploaded via HTTP curl POST.

## Deploying the Database

To deploy the database, use this command:

```bash
uvicorn main:app --reload
```bash


Uvicorn es un servidor ASGI ultrarrápido basado en uvloop y httptools. Forma parte del proyecto Starlette y es el servidor recomendado para FastAPI.

ASGI son las siglas de Asynchronous Server Gateway Interface. Es una interfaz estándar entre servidores web Python con capacidad asíncrona, frameworks y aplicaciones. Esto contrasta con WSGI (Web Server Gateway Interface), que es una interfaz estándar para aplicaciones web Python síncronas.

Uvicorn y FastAPI hacen posible el uso de programación asíncrona en su aplicación, lo que puede proporcionar mejoras significativas en el rendimiento de IO-bound y aplicaciones Python de alta concurrencia.

En el comando uvicorn main:app --reload, uvicorn es el servidor, main es el archivo Python (es decir, main.py), y app es el objeto creado por FastAPI para ejecutar su aplicación. La bandera --reload hace que el servidor se reinicie después de los cambios de código, por lo que es una gran opción durante el desarrollo.

Así que, en resumen, Uvicorn es un servidor ASGI para aplicaciones asíncronas Python, y se utiliza aquí para servir a su aplicación FastAPI.

	
	
