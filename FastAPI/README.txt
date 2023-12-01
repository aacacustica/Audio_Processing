Santiago Campo	07/07/2023

fast_api consiste en la creación y comunicación de una API y una Base de Datos para la estructuración y visualización de los datos obtenidos por el procesamiento de audios.



Existen dos carpetas:

	[1] fast_api > prueba
	
	Aquí se han hecho las pruebas necesarias para el entendimiento del framework FASTAPI y la herramienta de Base de Datos de SQLAlchemy.
	
	structure.txt está la estrutura de la Base de Datos que hay de desarrollar en SQLAlchemy.

	main.py - Aquí definismos la aplicación FastAPI, configuras el middleware e incluyes tus routers (endponits de la API). Los enrutadores suelen estar repartidos en diferentes archivos y se incluyen en la aplicación principal mediante app.include_router(). Este archivo es también donde gestionamos las sesiones de base de datos, manejando la apertura y cierre de sesiones para cada petición.

	models.py - Aquí es donde definimos los modelos SQLAlchemy. Estas son clases que se asignan a las tablas de la base de datos. Heredan de la clase Base que definiste en database.py y cada atributo de un modelo representa una columna de la tabla. Estos modelos se utilizan para crear, recuperar, actualizar y eliminar registros en la base de datos.

	schemas.py - Aquí es donde definimos los modelos Pydantic (esquemas). Estos modelos se utilizan para analizar y validar los datos JSON que la API envía y recibe. Utilizan anotaciones de tipo Python para definir el tipo esperado de cada campo en el modelo. FastAPI utiliza estos esquemas para generar automáticamente los documentos de la API y validar los datos de las solicitudes entrantes.

	crud.py - Son las siglas de Create, Read, Update, Delete, que son las operaciones básicas que puedes realizar en una base de datos. Este archivo contiene las funciones para interactuar con la base de datos, usando los modelos que definimos en models.py.


	[2] fast_api > api_db

	Aquí se ha desarrollado finalmente nuestra API y la Base de Datos. Contiene los mismos archivos que la anterior más:

	database.py - Este archivo configura el motor de base de datos SQLAlchemy y sessionmaker. Contiene todos los detalles para conectarte a la base de datos específica. El motor y el SessionLocal creados aquí se utilizan en el resto de la aplicación para interactuar con la base de datos.

	y un archivo de audio. El cual es objeto de una prueba de comunicación. Una vez desplegada las dos herramientas se comprobó que la comunicación existe creando un endponit que, al subir un archivo de audio por HTTP curl POST, o mejor, al recibir un archivo de audio, este es automaticamente almacenado en el disco local.

	

Para desplegar la base de datos se usa este comando:

	uvicorn main:app --reload

Uvicorn es un servidor ASGI ultrarrápido basado en uvloop y httptools. Forma parte del proyecto Starlette y es el servidor recomendado para FastAPI.

ASGI son las siglas de Asynchronous Server Gateway Interface. Es una interfaz estándar entre servidores web Python con capacidad asíncrona, frameworks y aplicaciones. Esto contrasta con WSGI (Web Server Gateway Interface), que es una interfaz estándar para aplicaciones web Python síncronas.

Uvicorn y FastAPI hacen posible el uso de programación asíncrona en su aplicación, lo que puede proporcionar mejoras significativas en el rendimiento de IO-bound y aplicaciones Python de alta concurrencia.

En el comando uvicorn main:app --reload, uvicorn es el servidor, main es el archivo Python (es decir, main.py), y app es el objeto creado por FastAPI para ejecutar su aplicación. La bandera --reload hace que el servidor se reinicie después de los cambios de código, por lo que es una gran opción durante el desarrollo.

Así que, en resumen, Uvicorn es un servidor ASGI para aplicaciones asíncronas Python, y se utiliza aquí para servir a su aplicación FastAPI.

	
	