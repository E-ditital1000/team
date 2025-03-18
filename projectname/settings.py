from pathlib import Path
import os
import environ

# Initialize environment variables
env = environ.Env()
environ.Env.read_env()  # This reads the .env file

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$v79hsag()wa5o#x#^yahn2exx)#18cd7q!f^4rd4^647(^k4jgca'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == ''

ALLOWED_HOSTS = ['smartmedia-t9s2.onrender.com', '.now.sh', '127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # Ensure WhiteNoise is added here
    'django.contrib.staticfiles', 
    'bloger',
    'cloudinary',
    'cloudinary_storage',
    'shop.apps.ShopConfig',  # Add this line
    'messaging.apps.MessagingConfig',
    'django_ckeditor_5',
  
]

# Cloudinary configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dhjk7yqhd',
    'API_KEY': '631711346737842',
    'API_SECRET': 'GPNuxhykDt1UMo0q4aVHlmVgs1k',
    'UPLOAD_OPTIONS': {
        'resource_type': 'auto',
        'invalidate': True,
    },
}



DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
WHITENOISE_AUTOREFRESH = True 

STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'
# Whitenoise Configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'projectname.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'projectname.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# Uncomment the PostgreSQL configuration and comment out the SQLite configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',
        'USER': 'postgres',
        'PASSWORD': 'atAUXOCydBRYRvgEfiBWuKXxkVeAuVtd',
        'HOST': 'autorack.proxy.rlwy.net',
        'PORT': '32405',
    }
}


DATABASES = {
    'default': {
        'ENGINE': env('DATABASE_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': str(env('DATABASE_NAME', default=BASE_DIR / 'db.sqlite3')),  # Convert to string
        'USER': env('DATABASE_USER', default=''),
        'PASSWORD': env('DATABASE_PASSWORD', default=''),
        'HOST': env('DATABASE_HOST', default=''),
        'PORT': env('DATABASE_PORT', default=''),
    }
}

# Comment out the SQLite configuration
#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': BASE_DIR / 'db.sqlite3',
#    }
#}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

# Static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# CKEditor upload paths
CKEDITOR_UPLOAD_PATH = 'uploads/ckeditor/'
CKEDITOR_5_UPLOAD_PATH = "uploads/ckeditor5/"

# File storage settings
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Image Backend
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_5_FILE_EXTENSIONS = ['jpg', 'png', 'gif', 'jpeg']

# Whitenoise Configuration
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript',
    # ... other mime types
}

# CKEditor 5 Configuration
CKEDITOR_5_CONFIGS = {
    'default': {
        # Comprehensive toolbar
        'toolbar': [
            'heading', '|',
            'bold', 'italic', 'link', 'bulletedList', 'numberedList', '|',
            'outdent', 'indent', '|',
            'blockQuote', 'imageUpload', 'insertTable', 'mediaEmbed', '|',
            'undo', 'redo', '|',
            'sourceEditing'
        ],
        
        # Responsive sizing
        'height': '400px',
        'width': '100%',
        
        # Localization
        'language': 'en',
        
        # Advanced Heading Options
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'},
            ]
        },
        
        # Image Toolbar
        'image': {
            'toolbar': [
                'imageStyle:inline',
                'imageStyle:block',
                'imageStyle:side',
                '|',
                'toggleImageCaption',
                'imageTextAlternative',
                '|',
                'linkImage'
            ],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]
        },
        
        # Table Configuration
        'table': {
            'contentToolbar': [
                'tableColumn', 
                'tableRow', 
                'mergeTableCells',
                'tableProperties', 
                'tableCellProperties'
            ]
        },
        
        # Link Configuration
        'link': {
            'decorators': {
                'openInNewTab': {
                    'mode': 'manual',
                    'label': 'Open in a new tab',
                    'attributes': {
                        'target': '_blank',
                        'rel': 'noopener noreferrer'
                    }
                }
            }
        },
        
        # File upload options
        'simpleUpload': {
            'uploadUrl': '/ckeditor5/upload/',
            'headers': {
                'X-CSRF-TOKEN': 'CSRF_TOKEN_PLACEHOLDER'
            }
        }
    }
}



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'django_error.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'bloger': {  # Your app name
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Additional settings
CKEDITOR_5_CUSTOM_CSS = None  # Optional: path to custom CSS
# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
