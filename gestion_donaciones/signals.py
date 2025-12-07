from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import (
    Donacion,
    Entrega,
    DetalleEntrega,
    ArticuloDonado,
    DetalleDonacion,
)


# ==========================================
# DETALLE DE DONACION (AUMENTAR / AJUSTAR STOCK)
# ==========================================


@receiver(pre_save, sender=DetalleDonacion)
def cache_detalle_donacion(sender, instance, **kwargs):
    """Guarda la cantidad previa para calcular diferencias al actualizar."""
    if instance.pk:
        try:
            original = DetalleDonacion.objects.get(pk=instance.pk)
            instance._cantidad_anterior = original.cantidad
        except DetalleDonacion.DoesNotExist:
            instance._cantidad_anterior = None
    else:
        instance._cantidad_anterior = None


@receiver(post_save, sender=DetalleDonacion)
def ajustar_stock_detalle_donacion(sender, instance, created, **kwargs):
    """
    Aumenta el stock cuando se crea un detalle de donacion
    y ajusta por diferencia cuando se edita.
    """
    articulo = instance.articulo

    if created:
        delta = instance.cantidad
    else:
        anterior = getattr(instance, "_cantidad_anterior", None)
        delta = instance.cantidad - anterior if anterior is not None else instance.cantidad

    if delta:
        articulo.cantidad += delta
        articulo.save()


@receiver(post_delete, sender=DetalleDonacion)
def restar_stock_al_eliminar_detalle_donacion(sender, instance, **kwargs):
    """
    Resta el stock cuando se elimina un detalle de donacion.
    """
    articulo = instance.articulo
    articulo.cantidad = max(0, articulo.cantidad - instance.cantidad)
    articulo.save()


# ==========================================
# DETALLE DE ENTREGA (DISMINUIR / AJUSTAR STOCK)
# ==========================================


@receiver(pre_save, sender=DetalleEntrega)
def cache_detalle_entrega(sender, instance, **kwargs):
    """Guarda la cantidad previa para calcular diferencias al actualizar."""
    if instance.pk:
        try:
            original = DetalleEntrega.objects.get(pk=instance.pk)
            instance._cantidad_anterior = original.cantidad
        except DetalleEntrega.DoesNotExist:
            instance._cantidad_anterior = None
    else:
        instance._cantidad_anterior = None


@receiver(post_save, sender=DetalleEntrega)
def actualizar_stock_detalle_entrega(sender, instance, created, **kwargs):
    """
    Resta stock cuando se registra o edita un detalle de entrega.
    """
    articulo = instance.articulo

    if created:
        delta = instance.cantidad
    else:
        anterior = getattr(instance, "_cantidad_anterior", None)
        delta = instance.cantidad - anterior if anterior is not None else instance.cantidad

    if delta:
        articulo.cantidad = max(0, articulo.cantidad - delta)
        articulo.save()


@receiver(post_delete, sender=DetalleEntrega)
def eliminar_detalle_entrega_actualiza_stock(sender, instance, **kwargs):
    """
    Restaura stock al eliminar un detalle de entrega.
    """
    articulo = instance.articulo
    articulo.cantidad += instance.cantidad
    articulo.save()


# ==========================================
# SIGNAL PARA ELIMINAR ENTREGA COMPLETA
# ==========================================


@receiver(post_delete, sender=Entrega)
def eliminar_entrega_completa(sender, instance, **kwargs):
    """
    Cuando se elimina una entrega completa, los detalles se eliminan en cascada
    y sus signals restauran el stock automaticamente.
    Este signal es solo para logging o acciones adicionales si se necesitan.
    """
    pass  # Los detalles se eliminan automaticamente por CASCADE
