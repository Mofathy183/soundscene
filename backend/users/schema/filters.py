import django_filters

from users.models import Profile, User
from users.utility import ALLOWED_SORT_FIELDS


class UserFilter(django_filters.FilterSet):
    username = django_filters.CharFilter(lookup_expr="icontains")
    name = django_filters.CharFilter(lookup_expr="icontains")
    email = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()
    is_staff = django_filters.BooleanFilter()

    # Use DateFromToRangeFilter for ranges: ?created_at_after=&created_at_before=
    date_joined = django_filters.DateFromToRangeFilter()
    created_at = django_filters.DateFromToRangeFilter()
    updated_at = django_filters.DateFromToRangeFilter()

    # Ordering
    order_by = django_filters.OrderingFilter(
        field_labels={
            key: key.replace("_", " ").title() for key in ALLOWED_SORT_FIELDS
        },
        fields=list(ALLOWED_SORT_FIELDS.items()),
    )

    class Meta:
        model = User
        fields = {
            "username": ["exact", "icontains"],
            "name": ["exact", "icontains"],
            "email": ["exact", "iexact"],
            "is_active": ["exact"],
            "is_staff": ["exact"],
            "date_joined": ["exact", "lt", "gt"],
            "created_at": ["exact", "lt", "gt"],
        }


class ProfileFilter(django_filters.FilterSet):
    birthday_date = django_filters.DateFromToRangeFilter()
    user__username = django_filters.CharFilter(lookup_expr="icontains")
    user__email = django_filters.CharFilter(lookup_expr="icontains")
    user__name = django_filters.CharFilter(lookup_expr="icontains")

    order_by = django_filters.OrderingFilter(
        fields=[
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("birthday_date", "birthday_date"),
        ],
        field_labels={
            "created_at": "Created At",
            "updated_at": "Updated At",
            "birthday_date": "Birthday Date",
        },
    )

    class Meta:
        model = Profile
        fields = {
            "birthday_date": ["exact", "gte", "lte"],
            "created_at": ["exact", "lt", "gt"],
        }
