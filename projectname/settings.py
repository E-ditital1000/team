from pathlib import Path
import os

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
    'django_select2',
    'cloudinary_storage',
    'shop.apps.ShopConfig',
    'chats.apps.ChatsConfig',
    'django_ckeditor_5',
     'crispy_forms',
    'channels',  # Add Channels
    'django_htmx',  # You already have the middleware, adding the app for consistency
]

# Add to the bottom of settings.py
CRISPY_TEMPLATE_PACK = 'bootstrap4'  # or 'bootstrap5' if using Bootstrap 5
# In settings.py
SELECT2_CACHE_BACKEND = 'default'

# Cloudinary configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dxfnt46gv',
    'API_KEY': '797951745846398',
    'API_SECRET': 'J1Yfn5bk8Nt9oG5k2jguZx-pD6U',
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
    "django_htmx.middleware.HtmxMiddleware", 
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
        'PASSWORD': 'ZHCtWrMEaeBOQxvWaYprwUOuwYdIcgHp',
        'HOST': 'caboose.proxy.rlwy.net',
        'PORT': '34589',
    }
}


#Comment out the SQLite configuration
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


# Configure Channel Layers
CHANNEL_LAYERS = {
    'default': {
        # For development, use the in-memory channel layer
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
        
        # For production, use Redis (requires channels_redis package)
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379/0')],
        # },
    }
}

# WebSocket authentication settings
WEBSOCKET_TIMEOUT = 3600  # 1 hour in seconds
WEBSOCKET_ACCEPT_ALL = True  # Accept all WebSocket connections (authentication is handled by middleware)

# ASGI configuration
ASGI_APPLICATION = 'projectname.asgi.application'

# HTMX Configuration (already included middleware)
HTMX_CLASSES = {
    'hx-indicator': 'htmx-indicator',
    'hx-swap-oob': 'htmx-swap-oob',
}

# Additional settings
CKEDITOR_5_CUSTOM_CSS = None  # Optional: path to custom CSS
# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
