import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from pitch.custom_fnc import convert_timedelta
from pitch.models import Pitch, Order
from django.utils import timezone
import datetime


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence("user{}".format)
    email = factory.Sequence("user{}@company.com".format)
    password = factory.PostGenerationMethodCall("set_password", "admin@123")
    is_superuser = False
    is_staff = True
    is_active = True


class PitchFactory(DjangoModelFactory):
    class Meta:
        model = Pitch

    address = factory.Faker("address")
    title = factory.Faker("name")
    description = factory.Faker("sentence", nb_words=40)
    phone = factory.Faker("phone_number")
    avg_rating = 0
    price = 1000000


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    time_start = timezone.now() + datetime.timedelta(days=1)

    time_end = factory.LazyAttribute(
        lambda o: o.time_start + datetime.timedelta(hours=1)
    )
    price = factory.LazyAttribute(lambda o: o.pitch.price)
    cost = factory.LazyAttribute(
        lambda o: o.pitch.price * convert_timedelta(o.time_end - o.time_start)
    )
