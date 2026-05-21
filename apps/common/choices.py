from django.db import models
from django.utils.translation import gettext_lazy as _

class StaffRole(models.TextChoices):
    SUPERADMIN = 'superadmin', _('Суперадмин')
    ADMIN = 'admin', _('Администратор')
    MANAGER = 'manager', _('Менеджер')
    OPERATOR = 'operator', _('Оператор')
    WAREHOUSE = 'warehouse', _('Складской сотрудник')

class ItemType(models.TextChoices):
    STANDARD = 'standard', _('Стандартный')
    ELECTRONICS = 'electronics', _('Электроника')
    CLOTHING = 'clothing', _('Одежда')
    FRAGILE = 'fragile', _('Хрупкий')
    DANGEROUS = 'dangerous', _('Опасный')

class TransportType(models.TextChoices):
    AUTO = 'auto', _('Авто')
    AVIA = 'avia', _('Авиа')
    RAIL = 'rail', _('Ж/Д')
    SEA = 'sea', _('Море')

class PaymentType(models.TextChoices):
    WEIGHT = 'weight', _('По весу')
    VOLUME = 'volume', _('По объему')
    FIXED = 'fixed', _('Фиксированный')
    MIXED = 'mixed', _('Смешанный')

class PaymentStatus(models.TextChoices):
    UNPAID = 'unpaid', _('Не оплачено')
    PARTIALLY_PAID = 'partially_paid', _('Частично оплачено')
    PAID = 'paid', _('Оплачено')
    REFUNDED = 'refunded', _('Возврат')

class DeliveryStatus(models.TextChoices):
    CREATED = 'created', _('Создан')
    AT_CHINA_WAREHOUSE = 'at_china_warehouse', _('На складе в Китае')
    MEASURED = 'measured', _('Измерен')
    PHOTOGRAPHED = 'photographed', _('Сфотографирован')
    LABELED = 'labeled', _('Маркирован')
    PACKED = 'packed', _('Упакован')
    GROUPED = 'grouped', _('Добавлен в партию')
    SENT_TO_URUMQI = 'sent_to_urumqi', _('Отправлен в Урумчи')
    ARRIVED_URUMQI = 'arrived_urumqi', _('Прибыл в Урумчи')
    SENT_TO_TURKMENISTAN = 'sent_to_turkmenistan', _('Отправлен в Туркменистан')
    ARRIVED_TURKMENISTAN = 'arrived_turkmenistan', _('Прибыл в Туркменистан')
    OUT_FOR_DELIVERY = 'out_for_delivery', _('На доставке')
    DELIVERED = 'delivered', _('Доставлен')
    CANCELLED = 'cancelled', _('Отменён')

class WarehouseStage(models.TextChoices):
    INTAKE = 'intake', _('Приёмка')
    MEASURED = 'measured', _('Измерение')
    PHOTOGRAPHED = 'photographed', _('Фото')
    LABELED = 'labeled', _('Маркировка')
    PACKED = 'packed', _('Упаковка')
    GROUPED = 'grouped', _('В партии')
    DISPATCHED = 'dispatched', _('Отправлен')

class CalculationType(models.TextChoices):
    WEIGHT = 'weight', _('За КГ')
    VOLUME = 'volume', _('За Куб')
    FIXED = 'fixed', _('Фиксированная')
    MIXED = 'mixed', _('Смешанная (Макс)')

class Currency(models.TextChoices):
    USD = 'USD', _('USD')
    CNY = 'CNY', _('CNY')
    TMT = 'TMT', _('TMT')
    UZS = 'UZS', _('UZS')

class ExpenseType(models.TextChoices):
    PACKAGING = 'packaging', _('Упаковка')
    STORAGE = 'storage', _('Хранение')
    INSURANCE = 'insurance', _('Страховка')
    CUSTOM = 'custom', _('Другое')

class ShipmentGroupStatus(models.TextChoices):
    DRAFT = 'draft', _('Черновик')
    FORMING = 'forming', _('Формируется')
    READY_TO_DISPATCH = 'ready_to_dispatch', _('Готов к отправке')
    IN_TRANSIT_TO_URUMQI = 'in_transit_to_urumqi', _('В пути в Урумчи')
    ARRIVED_URUMQI = 'arrived_urumqi', _('Прибыл в Урумчи')
    IN_TRANSIT_TO_TURKMENISTAN = 'in_transit_to_turkmenistan', _('В пути в Туркменистан')
    ARRIVED_TURKMENISTAN = 'arrived_turkmenistan', _('Прибыл в Туркменистан')
    COMPLETED = 'completed', _('Завершен')
    CANCELLED = 'cancelled', _('Отменён')

class PaymentMethod(models.TextChoices):
    CASH = 'cash', _('Наличные')
    CARD = 'card', _('Карта')
    BANK_TRANSFER = 'bank_transfer', _('Банковский перевод')
    WECHAT = 'wechat', _('WeChat')
    ALIPAY = 'alipay', _('Alipay')

class PaymentTransactionStatus(models.TextChoices):
    PENDING = 'pending', _('В ожидании')
    COMPLETED = 'completed', _('Завершен')
    FAILED = 'failed', _('Ошибка')
    CANCELLED = 'cancelled', _('Отменён')

class PaymentTransactionType(models.TextChoices):
    PAYMENT = 'payment', _('Платёж')
    REFUND = 'refund', _('Возврат')

class VolumeSource(models.TextChoices):
    CALCULATED = 'calculated', _('Рассчитан из габаритов')
    MANUAL = 'manual', _('Введён вручную')

class BoxStatus(models.TextChoices):
    OPEN = 'open', _('Открыта')
    CLOSED = 'closed', _('Закрыта')
    LABELED = 'labeled', _('Этикетка напечатана')

class AttachmentType(models.TextChoices):
    INVOICE = 'invoice', _('Инвойс')
    WAYBILL = 'waybill', _('Накладная')
    CUSTOMS_DOC = 'customs_doc', _('Таможенный документ')
    OTHER = 'other', _('Другое')
    IDENTITY_DOC = 'identity_doc', _('Identity Doc')
