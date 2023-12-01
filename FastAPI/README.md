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
```

Uvicorn is an ultra-fast ASGI server based on uvloop and httptools. It's part of the Starlette project and is the recommended server for FastAPI.

ASGI stands for Asynchronous Server Gateway Interface. It's a standard interface between Python web servers with asynchronous capability, frameworks, and applications. This contrasts with WSGI (Web Server Gateway Interface), which is a standard interface for synchronous Python web applications.

Uvicorn and FastAPI enable asynchronous programming in your application, which can offer significant performance improvements in IO-bound and high concurrency Python applications.

In the `uvicorn main:app --reload` command, `uvicorn` is the server, `main` is the Python file (i.e., `main.py`), and `app` is the object created by FastAPI to run your application. The `--reload` flag makes the server restart after code changes, making it a great option during development.

In summary, Uvicorn is an ASGI server for asynchronous Python applications, used here to serve your FastAPI application.