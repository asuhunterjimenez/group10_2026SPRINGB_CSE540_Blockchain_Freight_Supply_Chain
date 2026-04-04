
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'Jenik_freight_crm',           # your database name
        'USER': 'Jenik_freight_crm',         # your database user
        'PASSWORD': 'XAX@Nigeria@XNX', # your database password
        'HOST': 'localhost',      # or your db host/IP
        'PORT': '5433',           # default PostgreSQL port
    }
}



