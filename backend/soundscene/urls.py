"""
URL configuration for soundscene project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/

Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))

"""

from typing import List

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, path
from django.views.decorators.csrf import ensure_csrf_cookie
from graphene_django.views import GraphQLView
from graphql_jwt.decorators import jwt_cookie

urlpatterns: List[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    # Wrap GraphQL view with jwt_cookie to enable secure cookie auth
    path(
        "graphql/",
        ensure_csrf_cookie(jwt_cookie(GraphQLView.as_view(graphiql=True))),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
