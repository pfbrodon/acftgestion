from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from socios.models import Pago
from .models import MovimientoCaja, CategoriaMovimiento, TipoMovimiento

@receiver(post_save, sender=Pago)
def crear_movimiento_caja_pago(sender, instance, created, **kwargs):
    """
    Crear un movimiento de caja automáticamente cuando se registra un pago
    """
    if created:
        # Buscar o crear la categoría para ingresos por cuotas
        categoria_cuotas, _ = CategoriaMovimiento.objects.get_or_create(
            nombre="Cuotas Sociales",
            defaults={
                'tipo': TipoMovimiento.INGRESO,
                'descripcion': "Ingresos por pagos de cuotas de socios",
                'activo': True
            }
        )
        
        # Crear descripción detallada
        if instance.cuota:
            descripcion = f"Pago de cuota {instance.cuota} - {instance.socio.nombre} {instance.socio.apellido}"
        else:
            # Para pagos antiguos (sistema de conceptos)
            descripcion = f"Pago de {instance.concepto.nombre} - {instance.socio.nombre} {instance.socio.apellido}"
            if instance.mes_correspondiente and instance.año_correspondiente:
                descripcion += f" ({instance.mes_correspondiente}/{instance.año_correspondiente})"
        
        # Crear el movimiento de caja
        MovimientoCaja.objects.create(
            fecha=instance.fecha_pago,
            tipo=TipoMovimiento.INGRESO,
            categoria=categoria_cuotas,
            monto=instance.monto,
            descripcion=descripcion,
            pago=instance
        )

@receiver(post_delete, sender=Pago)
def eliminar_movimiento_caja_pago(sender, instance, **kwargs):
    """
    Eliminar el movimiento de caja cuando se elimina un pago
    """
    try:
        movimiento = MovimientoCaja.objects.get(pago=instance)
        movimiento.delete()
    except MovimientoCaja.DoesNotExist:
        # No hay movimiento asociado, no hacer nada
        pass
