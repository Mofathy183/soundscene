import graphene
from graphene_django import DjangoObjectType
from graphene import relay
from users.models import User, Profile
from .filters import UserFilter, ProfileFilter


class ProfileType(DjangoObjectType):
    age = graphene.Int()

    class Meta:
        model = Profile
        interfaces = (relay.Node,)
        filterset_class = ProfileFilter
        fields = (
            "id",
            "bio",
            "birthday_date",
            "age",
            "avatar",
            "created_at",
        )

    def resolve_age(self, info):
        return self.age  # This assumes `.age` is a @property or method in your model


class UserNode(DjangoObjectType):
    profile = graphene.Field(ProfileType)

    class Meta:
        model = User
        interfaces = (relay.Node,)
        filterset_class = UserFilter
        fields = (
            "id",
            "name",
            "username",
            "email",
            "date_joined",
            "created_at",
            "is_active",
        )

    def resolve_profile(self, info):
        return getattr(self, "profile", None)
