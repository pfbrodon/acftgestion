from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Socio, SaldoSocio, Pago, DetallePago, MovimientoSaldo

@receiver(post_save, sender=Socio)
def crear_saldo_socio(sender, instance, created, **kwargs):
    """Crear saldo inicial para nuevos socios"""
    if created:
        SaldoSocio.objects.get_or_create(
            socio=instance,
            defaults={'saldo_actual': 0}
        )

# Signal removido para evitar duplicación - la sincronización con caja se maneja en caja/signals.py

@receiver(post_delete, sender=Pago)
def eliminar_movimiento_caja_pago(sender, instance, **kwargs):
    """Eliminar movimiento de caja asociado al pago"""
    try:
        if hasattr(instance, 'movimientocaja'):
            instance.movimientocaja.delete()
    except Exception as e:
        print(f"Error al eliminar movimiento de caja: {e}")
