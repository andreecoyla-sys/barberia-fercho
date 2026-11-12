import os
import environ
import oscar

env = environ.Env()

# Path helper
location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

EMAIL_SUBJECT_PREFIX = '[Barberia Ecommerce] '
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Use a Sqlite database by default
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', location('db.sqlite')),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', None),
        'HOST': os.environ.get('DATABASE_HOST', None),
        'PORT': os.environ.get('DATABASE_PORT', None),
        'ATOMIC_REQUESTS': True
    }
}

CACHES = {
    'default': env.cache(default='locmemcache://'),
}

USE_TZ = True
TIME_ZONE = 'America/Lima'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

LANGUAGE_CODE = 'es'

gettext_noop = lambda s: s
LANGUAGES = (
    ('ar', gettext_noop('Arabic')),
    ('ca', gettext_noop('Catalan')),
    ('cs', gettext_noop('Czech')),
    ('da', gettext_noop('Danish')),
    ('de', gettext_noop('German')),
    ('en-gb', gettext_noop('British English')),
    ('el', gettext_noop('Greek')),
    ('es', gettext_noop('Spanish')),
    ('fi', gettext_noop('Finnish')),
    ('fr', gettext_noop('French')),
    ('it', gettext_noop('Italian')),
    ('ko', gettext_noop('Korean')),
    ('nl', gettext_noop('Dutch')),
    ('pl', gettext_noop('Polish')),
    ('pt', gettext_noop('Portuguese')),
    ('pt-br', gettext_noop('Brazilian Portuguese')),
    ('ro', gettext_noop('Romanian')),
    ('ru', gettext_noop('Russian')),
    ('sk', gettext_noop('Slovak')),
    ('uk', gettext_noop('Ukrainian')),
    ('zh-cn', gettext_noop('Simplified Chinese')),
)

SITE_ID = 1

USE_I18N = True
USE_L10N = True

MEDIA_ROOT = location("public/media")
MEDIA_URL = '/media/'

STATIC_URL = '/static/'
STATIC_ROOT = location('public/static')
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_DIRS = (
    location('static/'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECRET_KEY = env.str('SECRET_KEY', default='UajFCuyjDKmWHe29neauXzHi9eZoRXr6RMbT5JyAdPiACBP6Cra2')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('templates'),
        ],
        'OPTIONS': {
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                # Oscar specific
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.communication.notifications.context_processors.notifications',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ],
            'debug': DEBUG,
        }
    }
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.common.CommonMiddleware',
    'oscar.apps.basket.middleware.BasketMiddleware',
]

ROOT_URLCONF = 'urls'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s',
        },
        'simple': {
            'format': '[%(asctime)s] %(message)s'
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'oscar': {
            'level': 'DEBUG',
            'propagate': True,
        },
        'oscar.catalogue.import': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'oscar.alerts': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['null'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sorl.thumbnail': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',

    'oscar.config.Shop',
    'oscar.apps.analytics.apps.AnalyticsConfig',
    'oscar.apps.checkout.apps.CheckoutConfig',
    'oscar.apps.address.apps.AddressConfig',
    'oscar.apps.shipping.apps.ShippingConfig',
    'oscar.apps.catalogue.apps.CatalogueConfig',
    'oscar.apps.catalogue.reviews.apps.CatalogueReviewsConfig',
    'oscar.apps.communication.apps.CommunicationConfig',
    'oscar.apps.partner.apps.PartnerConfig',
    'oscar.apps.basket.apps.BasketConfig',
    'oscar.apps.payment.apps.PaymentConfig',
    'oscar.apps.offer.apps.OfferConfig',
    'oscar.apps.order.apps.OrderConfig',
    'oscar.apps.customer.apps.CustomerConfig',
    'oscar.apps.search.apps.SearchConfig',
    'oscar.apps.voucher.apps.VoucherConfig',
    'oscar.apps.wishlists.apps.WishlistsConfig',
    'oscar.apps.dashboard.apps.DashboardConfig',
    'oscar.apps.dashboard.reports.apps.ReportsDashboardConfig',
    'oscar.apps.dashboard.users.apps.UsersDashboardConfig',
    'oscar.apps.dashboard.orders.apps.OrdersDashboardConfig',
    'oscar.apps.dashboard.catalogue.apps.CatalogueDashboardConfig',
    'oscar.apps.dashboard.offers.apps.OffersDashboardConfig',
    'oscar.apps.dashboard.partners.apps.PartnersDashboardConfig',
    'oscar.apps.dashboard.pages.apps.PagesDashboardConfig',
    'oscar.apps.dashboard.ranges.apps.RangesDashboardConfig',
    'oscar.apps.dashboard.reviews.apps.ReviewsDashboardConfig',
    'oscar.apps.dashboard.vouchers.apps.VouchersDashboardConfig',
    'oscar.apps.dashboard.communications.apps.CommunicationsDashboardConfig',
    'oscar.apps.dashboard.shipping.apps.ShippingDashboardConfig',

    # 3rd-party apps that Oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'easy_thumbnails',
    'django_tables2',

    # Django apps that the sandbox depends on
    'django.contrib.sitemaps',

    # 3rd-party apps that the sandbox depends on
    'django_extensions',
    'debug_toolbar',
]

AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]

LOGIN_REDIRECT_URL = '/'
APPEND_SLASH = True

from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': location('whoosh_index'),
        'INCLUDE_SPELLING': True,
    },
}

INTERNAL_IPS = ['127.0.0.1', '::1']

from oscar.defaults import *

# Meta - Nombre y eslogan de tu Barberia
OSCAR_SHOP_NAME = 'Barbería Estilo Clásico'
OSCAR_SHOP_TAGLINE = 'Productos profesionales para barba y cabello'
OSCAR_DEFAULT_CURRENCY = 'PEN'

OSCAR_RECENTLY_VIEWED_PRODUCTS = 20
OSCAR_ALLOW_ANON_CHECKOUT = True

OSCAR_INITIAL_ORDER_STATUS = 'Pending'
OSCAR_INITIAL_LINE_STATUS = 'Pending'

OSCAR_ORDER_STATUS_PIPELINE = {
    'Pending': ('Being processed', 'Cancelled',),
    'Being processed': ('Complete', 'Cancelled',),
    'Cancelled': (),
    'Complete': (),
}

OSCAR_ORDER_STATUS_CASCADE = {
    'Being processed': 'Being processed',
    'Cancelled': 'Cancelled',
    'Complete': 'Shipped',
}

THUMBNAIL_DEBUG = DEBUG
THUMBNAIL_KEY_PREFIX = 'oscar-sandbox'
THUMBNAIL_KVSTORE = env(
    'THUMBNAIL_KVSTORE',
    default='sorl.thumbnail.kvstores.cached_db_kvstore.KVStore')
THUMBNAIL_REDIS_URL = env('THUMBNAIL_REDIS_URL', default=None)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

try:
    from settings_local import *
except ImportError:
    pass