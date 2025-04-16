"""
ASGI config for projectname project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
import datetime
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from channels.db import database_sync_to_async
import chats.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectname.settings')

# Get the base HTTP application
http_application = get_asgi_application()

# Custom authentication middleware to replace AuthMiddlewareStack
class CustomAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner
    
    async def __call__(self, scope, receive, send):
        # Add session and user to scope
        if "session" not in scope:
            scope["session"] = {}
            
        if "user" not in scope:
            scope["user"] = AnonymousUser()
            
        # Get session from cookies if available
        if "headers" in scope:
            headers = dict(scope["headers"])
            if b'cookie' in headers:
                cookies = headers[b'cookie'].decode()
                # Parse session cookie if present
                session_key = None
                for cookie in cookies.split('; '):
                    if cookie.startswith('sessionid='):
                        session_key = cookie.split('=')[1]
                        break
                
                if session_key:
                    # Get session and user using the session key
                    @database_sync_to_async
                    def get_user(session_key):
                        try:
                            session = Session.objects.get(
                                session_key=session_key,
                                expire_date__gt=datetime.datetime.now()
                            )
                            user_id = session.get_decoded().get('_auth_user_id')
                            if user_id:
                                from django.contrib.auth import get_user_model
                                User = get_user_model()
                                try:
                                    return User.objects.get(pk=user_id)
                                except User.DoesNotExist:
                                    pass
                        except Session.DoesNotExist:
                            pass
                        return AnonymousUser()
                    
                    scope["user"] = await get_user(session_key)
        
        return await self.inner(scope, receive, send)

# Application that routes based on type
application = ProtocolTypeRouter({
    "http": http_application,
    "websocket": SessionMiddlewareStack(
        CustomAuthMiddleware(
            URLRouter(
                chats.routing.websocket_urlpatterns,
            )
        )
    ),
})