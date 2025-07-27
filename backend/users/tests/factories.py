import factory
import re
from factory.fuzzy import FuzzyDate
from faker import Faker
from factory.django import DjangoModelFactory, ImageField
from django.contrib.auth.hashers import make_password
from users.models import User, Profile
from datetime import date
from dateutil.relativedelta import relativedelta


fake = Faker()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    username = factory.LazyFunction(
        lambda: re.sub(r"[^\w.-]", "", fake.user_name())[:30]
    )
    name = factory.LazyFunction(lambda: re.sub(r"[^a-zA-Z ]", "", fake.name())[:50])
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.LazyFunction(lambda: make_password("PassW0rd122?!"))

    @classmethod
    def create_with_raw_password(cls, password: str) -> User:
        return cls.build(
            username=re.sub(r"[^\w.-]", "", fake.user_name())[:30],
            name=re.sub(r"[^a-zA-Z ]", "", fake.name())[:50],
            email=fake.email(),
            password=password,
        )

    @classmethod
    def create_with_username(cls, username: str) -> User:
        return cls.build(
            username=username,
            name=re.sub(r"[^a-zA-Z ]", "", fake.name())[:50],
            email=fake.email(),
            password="PassW0rd122?!",
        )

    @classmethod
    def create_with_name(cls, name: str) -> User:
        return cls.build(
            username=re.sub(r"[^\w.-]", "", fake.user_name())[:30],
            name=name,
            email=fake.email(),
            password="PassW0rd122?!",
        )

    @classmethod
    def create_with_email(cls, email: str) -> User:
        return cls.build(
            username=re.sub(r"[^\w.-]", "", fake.user_name())[:30],
            name=re.sub(r"[^a-zA-Z ]", "", fake.name())[:50],
            email=email,
            password="PassW0rd122?!",
        )


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    birthday_date = FuzzyDate(
        start_date=date.today() - relativedelta(years=90),
        end_date=date.today() - relativedelta(years=12),
    )
    bio = factory.Faker("paragraph", nb_sentences=1)
    avatar = ImageField(width=100, height=100, color="blue")

    @classmethod
    def create_with_bio(cls, bio: str | int):
        return cls.create(bio=bio, user=UserFactory())

    @classmethod
    def create_with_birthday_date(cls, birthday_date: date | None):
        return cls.create(birthday_date=birthday_date, user=UserFactory())

    @classmethod
    def create_avatar_image(cls, avatar: int | str):
        return cls.create(avatar=avatar, user=UserFactory())
