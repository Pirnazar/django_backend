import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.locations.models import Destination, Warehouse
from apps.clients.models import Client
from apps.pricing.models import PriceRule
from apps.shipments.models import ShipmentGroup
from apps.items.models import Item, ItemExpense
from apps.payments.models import PaymentTransaction
from apps.common.choices import StaffRole, CalculationType

User = get_user_model()

class StaffUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    full_name = factory.Faker('name')
    role = StaffRole.OPERATOR
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or 'password123'
        self.set_password(password)
        if create:
            self.save()

class DestinationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Destination

    code = factory.Sequence(lambda n: f'DST{n}')
    name = factory.Faker('city')
    country_name = factory.Faker('country')
    is_active = True

class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    code = factory.Sequence(lambda n: f'WH{n}')
    name = factory.Faker('company')
    country = factory.Faker('country')
    city = factory.Faker('city')
    address = factory.Faker('address')
    is_active = True

class ClientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Client

    client_code = factory.Sequence(lambda n: f'CL{n:05d}')
    full_name = factory.Faker('name')
    phone_number = factory.Sequence(lambda n: f'+1234567890{n}'[:20])
    default_destination = factory.SubFactory(DestinationFactory)
    is_active = True

class PriceRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PriceRule

    destination = factory.SubFactory(DestinationFactory)
    name = factory.Sequence(lambda n: f'Rule {n}')
    calculation_type = CalculationType.WEIGHT
    price_per_kg = 5.00
    price_per_m3 = 100.00
    is_active = True

class ShipmentGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShipmentGroup

    group_code = factory.Sequence(lambda n: f'GRP{n:06d}')
    destination = factory.SubFactory(DestinationFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    created_by = factory.SubFactory(StaffUserFactory)

class ItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Item

    item_code = factory.Sequence(lambda n: f'ITM{n:07d}')
    client = factory.SubFactory(ClientFactory)
    destination = factory.SubFactory(DestinationFactory)
    warehouse = factory.SubFactory(WarehouseFactory)
    weight_kg = 10.00
    created_by = factory.SubFactory(StaffUserFactory)

class ItemExpenseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemExpense

    item = factory.SubFactory(ItemFactory)
    expense_type = 'custom'
    amount = 5.00
    created_by = factory.SubFactory(StaffUserFactory)

class PaymentTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentTransaction

    item = factory.SubFactory(ItemFactory)
    client = factory.SelfAttribute('item.client')
    amount = 50.00
    created_by = factory.SubFactory(StaffUserFactory)
