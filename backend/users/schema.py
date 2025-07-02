import graphene
from graphene_django.types import DjangoObjectType
from users.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "username", "email", "password")


class Query(graphene.ObjectType):
    pass
