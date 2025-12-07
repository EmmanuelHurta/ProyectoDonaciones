



-Dependencias principales

asgiref==3.9.1
bcrypt==5.0.0
Django==5.2.5
django-environ==0.12.0
mysqlclient==2.2.7
pillow==11.3.0
PyMySQL==1.1.2
sqlparse==0.5.3
tzdata==2025.2



-Estructura de Carpetas

MI_PROYECTO/
├── gestion_donaciones/          # Aplicación principal
│   ├── migrations/              # Migraciones de base de datos
│   ├── static/                  # Archivos estáticos CSS
│   │   └── DonacionesApp/
│   │       └── estilos.css
│   ├── Templates/               # Plantillas HTML
│   │   └── DonacionesApp/
│   │       ├── donaciones/      # Templates de donaciones
│   │       ├── entregas/        # Templates de entregas
│   │       ├── Login/           # Templates de autenticación
│   │       ├── Main/            # Template principal
│   │       ├── Registro/        # Templates de registro
│   │       ├── stock/           # Templates de stock
│   │       └── usuarios/        # Templates de usuarios
│   ├── __init__.py
│   ├── admin.py                 # Configuración del admin
│   ├── apps.py                  # Configuración de la app
│   ├── forms.py                 # Formularios Django
│   ├── models.py                # Modelos de datos
│   ├── tests.py                 # Tests
│   ├── urls.py                  # URLs de la aplicación
│   └── views.py                 # Vistas y lógica
├── ml_proyecto/                 # Configuración del proyecto
│   ├── __pycache__/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Configuración principal
│   ├── urls.py                  # URLs principales
│   └── wsgi.py
├── .env                         # Variables de entorno (no incluir en git)
├── manage.py                    # Script de gestión Django
├── gestion_donaciones_donacion.sql  # Script SQL
├── usuarios_grupos.json         # Datos de grupos de usuarios
└── README.md      


INSTRUCCIONES DE LA INSTALACION

Para importar usuarios y grupos con los privilegios creados con django Admin, se debe asegurar de que estén codificados en UTF-8 antes de cargarlos y luwgo aplicar el siguiente comando

python manage.py loaddata usuarios_backup.json

-Migraciones iniciales

python manage.py makemigrations
python manage.py migrate


-Inicia el servidor local de Django
python manage.py runserver




