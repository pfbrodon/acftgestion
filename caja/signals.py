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
        if instance.es_pago_multiple:
            # Para pagos múltiples, usar información de los detalles
            descripcion = f"Pago múltiple - {instance.socio.nombre} {instance.socio.apellido}"
        elif instance.cuota:
            descripcion = f"Pago de cuota {instance.cuota} - {instance.socio.nombre} {instance.socio.apellido}"
        elif instance.concepto:
            # Para pagos antiguos (sistema de conceptos)
            descripcion = f"Pago de {instance.concepto.nombre} - {instance.socio.nombre} {instance.socio.apellido}"
            if hasattr(instance, 'mes_correspondiente') and instance.mes_correspondiente:
                descripcion += f" ({instance.mes_correspondiente})"
        else:
            # Fallback para casos no esperados
            descripcion = f"Pago - {instance.socio.nombre} {instance.socio.apellido}"
        
        # Calcular montos para transparencia contable
        monto_efectivo = instance.monto - (instance.monto_saldo_usado or 0)
        monto_saldo_usado = instance.monto_saldo_usado or 0
        
        # Mejorar descripción para incluir información de saldo si se usó
        if monto_saldo_usado > 0:
            descripcion += f" (Efectivo: ${monto_efectivo}, Saldo usado: ${monto_saldo_usado})"
        
        # Crear el movimiento de caja con el monto TOTAL del pago
        # Esto mantiene la consistencia contable ya que el saldo a favor
        # representa dinero que ya estaba disponible en la organización
        MovimientoCaja.objects.create(
            fecha=instance.fecha_pago,
            tipo=TipoMovimiento.INGRESO,
            categoria=categoria_cuotas,
            monto=instance.monto,  # Monto total, no solo efectivo
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
