"""Box Builder — admin views for creating a Box by scanning barcodes."""
import json
import logging
from functools import wraps

from django.contrib import admin
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.common.choices import StaffRole
from apps.common.services import generate_box_code
from .models import Box
from .serializers import BoxSerializer
from .services import add_item_to_box, close_box, mark_box_printed, BoxScanError

logger = logging.getLogger(__name__)

_BUILDER_ROLES = {StaffRole.SUPERADMIN, StaffRole.ADMIN, StaffRole.MANAGER, StaffRole.OPERATOR, StaffRole.WAREHOUSE}


def _auth(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Требуется авторизация'}, status=401)
        if not request.user.is_staff:
            return JsonResponse({'error': 'Нет доступа'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


class BoxBuilderView(View):
    @method_decorator(_auth)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        context = {
            **admin.site.each_context(request),
            'title': 'Конструктор коробки',
            'suggested_code': generate_box_code(),
        }
        return TemplateResponse(request, 'admin/items/box_builder.html', context)


class BoxBuilderCreateView(View):
    @method_decorator(_auth)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        try:
            data = json.loads(request.body or '{}')
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Неверный формат данных'}, status=400)

        box_code = (data.get('box_code') or '').strip() or generate_box_code()
        barcode = (data.get('barcode') or '').strip() or box_code
        comment = data.get('comment', '')

        box = Box.objects.create(
            box_code=box_code,
            barcode=barcode,
            comment=comment,
            created_by=request.user,
        )
        return JsonResponse(BoxSerializer(box).data)


class BoxBuilderScanView(View):
    @method_decorator(_auth)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, box_id):
        try:
            data = json.loads(request.body or '{}')
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Неверный формат данных'}, status=400)

        try:
            box = Box.objects.get(pk=box_id)
        except Box.DoesNotExist:
            return JsonResponse({'error': 'Коробка не найдена'}, status=404)

        try:
            add_item_to_box(box, data.get('barcode'), user=request.user)
        except BoxScanError as e:
            return JsonResponse({'error': str(e)}, status=400)
        box.refresh_from_db()
        return JsonResponse(BoxSerializer(box).data)


class BoxBuilderRemoveView(View):
    @method_decorator(_auth)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, box_id):
        try:
            data = json.loads(request.body or '{}')
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Неверный формат данных'}, status=400)

        try:
            box = Box.objects.get(pk=box_id)
        except Box.DoesNotExist:
            return JsonResponse({'error': 'Коробка не найдена'}, status=404)

        item_id = data.get('item_id')
        item = box.items.filter(pk=item_id).first()
        if not item:
            return JsonResponse({'error': 'Груз не найден в коробке'}, status=400)
        item.box = None
        item.save(update_fields=['box', 'updated_by'])
        from .services import recalculate_box_totals
        recalculate_box_totals(box)
        box.refresh_from_db()
        return JsonResponse(BoxSerializer(box).data)


class BoxBuilderCloseView(View):
    @method_decorator(_auth)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, box_id):
        try:
            box = Box.objects.get(pk=box_id)
        except Box.DoesNotExist:
            return JsonResponse({'error': 'Коробка не найдена'}, status=404)
        try:
            close_box(box, user=request.user)
        except BoxScanError as e:
            return JsonResponse({'error': str(e)}, status=400)
        return JsonResponse(BoxSerializer(box).data)


class BoxBuilderPrintedView(View):
    @method_decorator(_auth)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, box_id):
        try:
            box = Box.objects.get(pk=box_id)
        except Box.DoesNotExist:
            return JsonResponse({'error': 'Коробка не найдена'}, status=404)
        mark_box_printed(box)
        return JsonResponse(BoxSerializer(box).data)
