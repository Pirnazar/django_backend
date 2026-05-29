"""
End-to-end tests for the client mobile portal:
register → login by phone → profile → services → cargo services → item nesting.
"""
import pytest
from rest_framework.test import APIClient

from apps.clients.models import Client, AdditionalService, CargoService
from apps.common.choices import StaffRole
from apps.common.factories import ItemFactory, ClientFactory, StaffUserFactory


@pytest.fixture
def api():
    return APIClient()


def _make_client_user(**client_kwargs):
    user = StaffUserFactory(role=StaffRole.CLIENT, is_staff=False)
    client = ClientFactory(user=user, **client_kwargs)
    return user, client


# ── Registration ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_register_creates_client_and_returns_jwt(api):
    resp = api.post('/api/v1/auth/register/', {
        'full_name': 'Иван Тестов',
        'phone_number': '+99361000111',
        'password': 'secret123',
    }, format='json')
    assert resp.status_code == 201
    data = resp.json()
    assert data['access'] and data['refresh']
    assert data['client_code']
    assert data['phone_number'] == '+99361000111'

    from django.contrib.auth import get_user_model
    U = get_user_model()
    user = U.objects.get(phone_number='+99361000111')
    assert user.role == StaffRole.CLIENT
    assert not user.is_staff
    assert Client.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_register_duplicate_phone_rejected(api):
    payload = {'full_name': 'A', 'phone_number': '+99361222333', 'password': 'secret123'}
    assert api.post('/api/v1/auth/register/', payload, format='json').status_code == 201
    resp = api.post('/api/v1/auth/register/', payload, format='json')
    assert resp.status_code == 400


# ── Login by phone / client_code ──────────────────────────────────────────────

@pytest.mark.django_db
def test_login_by_phone_after_register(api):
    api.post('/api/v1/auth/register/', {
        'full_name': 'Пол Тестов', 'phone_number': '+99361555000', 'password': 'secret123',
    }, format='json')
    resp = api.post('/api/v1/auth/login/', {
        'username': '+99361555000', 'password': 'secret123',
    }, format='json')
    assert resp.status_code == 200
    assert resp.json()['access']


@pytest.mark.django_db
def test_login_by_client_code(api):
    user, client = _make_client_user()
    user.set_password('mypass123')
    user.save()
    resp = api.post('/api/v1/auth/login/', {
        'username': client.client_code, 'password': 'mypass123',
    }, format='json')
    assert resp.status_code == 200


# ── Profile ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_profile_get(api):
    user, client = _make_client_user()
    api.force_authenticate(user=user)
    resp = api.get('/api/v1/client/profile/')
    assert resp.status_code == 200
    data = resp.json()
    assert data['client_code'] == client.client_code
    assert data['phone'] == client.phone_number


@pytest.mark.django_db
def test_profile_patch(api):
    user, client = _make_client_user()
    api.force_authenticate(user=user)
    resp = api.patch('/api/v1/client/profile/', {
        'full_name': 'Новое Имя',
        'whatsapp': '+99361999888',
        'preferred_language': 'tk',
        'note': 'позвоните заранее',
    }, format='json')
    assert resp.status_code == 200
    client.refresh_from_db()
    assert client.full_name == 'Новое Имя'
    assert client.whatsapp == '+99361999888'
    assert client.preferred_language == 'tk'
    assert client.notes == 'позвоните заранее'


@pytest.mark.django_db
def test_profile_404_for_non_client(api):
    staff = StaffUserFactory(role=StaffRole.OPERATOR, is_staff=True)
    api.force_authenticate(user=staff)
    assert api.get('/api/v1/client/profile/').status_code == 404


@pytest.mark.django_db
def test_profile_patch_phone_syncs_user(api):
    user, client = _make_client_user()
    api.force_authenticate(user=user)
    resp = api.patch('/api/v1/client/profile/', {
        'phone_number': '+99361777666',
    }, format='json')
    assert resp.status_code == 200
    client.refresh_from_db()
    user.refresh_from_db()
    assert client.phone_number == '+99361777666'
    assert user.phone_number == '+99361777666'


@pytest.mark.django_db
def test_profile_patch_phone_duplicate_rejected(api):
    user, client = _make_client_user()
    other_user, other_client = _make_client_user(phone_number='+99361000000')
    api.force_authenticate(user=user)
    resp = api.patch('/api/v1/client/profile/', {
        'phone_number': '+99361000000',
    }, format='json')
    assert resp.status_code == 400


@pytest.mark.django_db
def test_profile_photo_upload(api):
    from django.core.files.uploadedfile import SimpleUploadedFile
    # 1x1 PNG
    png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00'
        b'\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    user, client = _make_client_user()
    api.force_authenticate(user=user)
    photo = SimpleUploadedFile('avatar.png', png, content_type='image/png')
    resp = api.patch('/api/v1/client/profile/', {'profile_photo': photo}, format='multipart')
    assert resp.status_code == 200
    assert resp.json()['photo_url']
    client.refresh_from_db()
    assert client.profile_photo


@pytest.mark.django_db
def test_change_password(api):
    user, client = _make_client_user()
    user.set_password('oldpass123')
    user.save()
    api.force_authenticate(user=user)
    resp = api.post('/api/v1/auth/change-password/', {
        'old_password': 'oldpass123', 'new_password': 'newpass456',
    }, format='json')
    assert resp.status_code == 200
    user.refresh_from_db()
    assert user.check_password('newpass456')


@pytest.mark.django_db
def test_change_password_wrong_old(api):
    user, client = _make_client_user()
    user.set_password('oldpass123')
    user.save()
    api.force_authenticate(user=user)
    resp = api.post('/api/v1/auth/change-password/', {
        'old_password': 'WRONG', 'new_password': 'newpass456',
    }, format='json')
    assert resp.status_code == 400


# ── Additional services ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_services_list_only_active(api):
    user, _ = _make_client_user()
    AdditionalService.objects.create(name='Упаковка', price=5, currency='USD')
    AdditionalService.objects.create(name='Скрытая', price=1, currency='USD', is_active=False)
    api.force_authenticate(user=user)
    resp = api.get('/api/v1/client/services/')
    assert resp.status_code == 200
    names = [s['name'] for s in resp.json()]
    assert 'Упаковка' in names
    assert 'Скрытая' not in names
    # price must be a JSON number (Double), not a string
    assert isinstance(resp.json()[0]['price'], (int, float))


@pytest.mark.django_db
def test_cargo_service_create_and_list(api):
    user, client = _make_client_user()
    item = ItemFactory(client=client)
    service = AdditionalService.objects.create(name='Фото', price=2, currency='USD')
    api.force_authenticate(user=user)

    resp = api.post(f'/api/v1/client/cargos/{item.id}/services/', {
        'service_id': service.id, 'comment': 'нужно срочно',
    }, format='json')
    assert resp.status_code == 201
    body = resp.json()
    assert body['service_name'] == 'Фото'
    assert isinstance(body['id'], str)
    assert body['status'] == 'pending'

    listing = api.get(f'/api/v1/client/cargos/{item.id}/services/')
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert CargoService.objects.filter(cargo=item, client=client).count() == 1


@pytest.mark.django_db
def test_client_cannot_access_others_cargo(api):
    user, client = _make_client_user()
    other_item = ItemFactory()  # belongs to a different client
    service = AdditionalService.objects.create(name='Фото', price=2)
    api.force_authenticate(user=user)

    assert api.get(f'/api/v1/client/cargos/{other_item.id}/services/').status_code == 404
    resp = api.post(f'/api/v1/client/cargos/{other_item.id}/services/', {
        'service_id': service.id,
    }, format='json')
    assert resp.status_code == 404


# ── Item nesting (mobile contract) ────────────────────────────────────────────

@pytest.mark.django_db
def test_item_detail_returns_nested_objects(api):
    user, client = _make_client_user()
    item = ItemFactory(client=client)
    api.force_authenticate(user=user)
    resp = api.get(f'/api/v1/items/{item.id}/')
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data['client'], dict)
    assert data['client']['client_code'] == client.client_code
    assert isinstance(data['destination'], dict)
    assert 'name' in data['destination']
    assert isinstance(data['warehouse'], dict)
    assert 'name' in data['warehouse']


@pytest.mark.django_db
def test_item_list_scoped_to_client(api):
    user, client = _make_client_user()
    ItemFactory(client=client)
    ItemFactory()  # other client's item
    api.force_authenticate(user=user)
    resp = api.get('/api/v1/items/')
    assert resp.status_code == 200
    results = resp.json()['results']
    assert len(results) == 1
    assert results[0]['client']['client_code'] == client.client_code
