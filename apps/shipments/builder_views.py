"""
Shipment Group Builder — admin views.
"""
import json
import logging
from functools import wraps

from django.contrib import admin
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.common.choices import DeliveryStatus, ShipmentGroupStatus, StaffRole
from apps.common.services import generate_group_code
from apps.items.models import Item, ItemStatusHistory
from apps.locations.models import Destination, Warehouse
from apps.shipments.models import ShipmentGroup
from apps.shipments.services import recalculate_shipment_group_totals

logger = logging.getLogger(__name__)

_BUILDER_ROLES = {StaffRole.SUPERADMIN, StaffRole.ADMIN, StaffRole.MANAGER, StaffRole.OPERATOR}
_EXCLUDE_STATUSES = {DeliveryStatus.DELIVERED, DeliveryStatus.CANCELLED}


def _builder_auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


class GroupBuilderView(View):
    """Main page — renders the builder template."""

    @method_decorator(_builder_auth)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            'title': 'Конструктор партии',
            'destinations': Destination.objects.filter(is_active=True).order_by('name'),
            'warehouses': Warehouse.objects.filter(is_active=True).order_by('name'),
            'status_choices': [
                (ShipmentGroupStatus.FORMING, 'Формируется'),
                (ShipmentGroupStatus.READY_TO_DISPATCH, 'Готов к отправке'),
            ],
            'suggested_code': generate_group_code(),
        }
        return TemplateResponse(request, 'admin/shipments/group_builder.html', context)


class GroupBuilderItemsView(View):
    """AJAX — returns JSON list of ungrouped items for given dest+wh."""

    @method_decorator(_builder_auth)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        dest_id = request.GET.get('destination_id')
        wh_id = request.GET.get('warehouse_id')

        if not dest_id or not wh_id:
            return JsonResponse({'items': []})

        qs = (
            Item.objects
            .filter(
                destination_id=dest_id,
                warehouse_id=wh_id,
                shipment_group__isnull=True,
            )
            .exclude(delivery_status__in=list(_EXCLUDE_STATUSES))
            .select_related('client', 'destination', 'warehouse')
            .order_by('-created_at')[:200]
        )

        items = [
            {
                'id': item.pk,
                'item_code': item.item_code,
                'client_code': item.client.client_code,
                'client_name': item.client.full_name,
                'weight_kg': float(item.weight_kg),
                'volume_m3': float(item.volume_m3),
                'total_price': float(item.total_price),
                'payment_status': item.get_payment_status_display(),
                'delivery_status': item.get_delivery_status_display(),
                'delivery_status_raw': item.delivery_status,
                'created_at': item.created_at.strftime('%d.%m.%Y') if item.created_at else '',
            }
            for item in qs
        ]
        return JsonResponse({'items': items})


class GroupBuilderCreateView(View):
    """POST JSON — creates ShipmentGroup and assigns items."""

    @method_decorator(_builder_auth)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Неверный формат данных'}, status=400)

        dest_id    = data.get('destination_id')
        wh_id      = data.get('warehouse_id')
        item_ids   = data.get('item_ids', [])
        group_code = (data.get('group_code') or '').strip()
        comment    = data.get('comment', '')
        status     = data.get('status', ShipmentGroupStatus.FORMING)

        if not dest_id or not wh_id:
            return JsonResponse({'error': 'Укажите направление и склад'}, status=400)
        if not item_ids:
            return JsonResponse({'error': 'Выберите хотя бы один груз'}, status=400)
        if status not in (ShipmentGroupStatus.FORMING, ShipmentGroupStatus.READY_TO_DISPATCH):
            status = ShipmentGroupStatus.FORMING

        try:
            destination = Destination.objects.get(pk=dest_id)
            warehouse   = Warehouse.objects.get(pk=wh_id)
        except (Destination.DoesNotExist, Warehouse.DoesNotExist):
            return JsonResponse({'error': 'Направление или склад не найдены'}, status=400)

        # Validate all items belong to this dest+wh and are ungrouped
        items_qs = Item.objects.filter(
            pk__in=item_ids,
            destination=destination,
            warehouse=warehouse,
            shipment_group__isnull=True,
        ).exclude(delivery_status__in=list(_EXCLUDE_STATUSES))

        if items_qs.count() != len(item_ids):
            return JsonResponse(
                {'error': 'Некоторые грузы недоступны (уже в партии, доставлены или несовместимы)'},
                status=400,
            )

        if not group_code:
            group_code = generate_group_code()

        group = ShipmentGroup.objects.create(
            group_code=group_code,
            destination=destination,
            warehouse=warehouse,
            status=status,
            comment=comment,
            created_by=request.user,
            updated_by=request.user,
        )

        # Bulk-assign items; queryset.update() bypasses signals so we recalculate manually
        items_qs.update(shipment_group=group)

        # Transition PACKED items → GROUPED and create history records
        packed_items = Item.objects.filter(
            pk__in=item_ids,
            delivery_status=DeliveryStatus.PACKED,
        )
        history_bulk = []
        for item in packed_items:
            history_bulk.append(ItemStatusHistory(
                item=item,
                old_status=DeliveryStatus.PACKED,
                new_status=DeliveryStatus.GROUPED,
                comment=f'Добавлен в партию {group_code} через конструктор',
                changed_by=request.user,
            ))
        if history_bulk:
            ItemStatusHistory.objects.bulk_create(history_bulk)
            packed_items.update(
                delivery_status=DeliveryStatus.GROUPED,
                warehouse_stage='grouped',
            )

        recalculate_shipment_group_totals(group)

        admin_url = f'/admin/shipments/shipmentgroup/{group.pk}/change/'
        return JsonResponse({
            'success': True,
            'group_id': group.pk,
            'group_code': group.group_code,
            'admin_url': admin_url,
            'total_items': group.total_items,
        })
