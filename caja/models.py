from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class TipoMovimiento(models.TextChoices):
    INGRESO = 'ingreso', 'Ingreso'
    EGRESO = 'egreso', 'Egreso'

class CategoriaMovimiento(models.Model):
    """Categorías para clasificar los movimientos de caja"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(
        max_length=10,
        choices=TipoMovimiento.choices,
        help_text="Tipo de movimiento: Ingreso o Egreso"
    )
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Categoría de Movimiento"
        verbose_name_plural = "Categorías de Movimientos"
        ordering = ['tipo', 'nombre']
    
    def __str__(self):
        return f"{self.get_tipo_display()}: {self.nombre}"

class MovimientoCaja(models.Model):
    """Registro de todos los movimientos de caja (ingresos y egresos)"""
    fecha = models.DateField()
    tipo = models.CharField(
        max_length=10,
        choices=TipoMovimiento.choices
    )
    categoria = models.ForeignKey(
        CategoriaMovimiento,
        on_delete=models.PROTECT,
        help_text="Categoría del movimiento"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    descripcion = models.TextField(
        help_text="Descripción detallada del movimiento"
    )
    
    # Relación con el pago (para ingresos por cuotas)
    pago = models.OneToOneField(
        'socios.Pago',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text="Pago asociado (solo para ingresos por cuotas)"
    )
    
    # Metadatos de auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ['-fecha', '-fecha_creacion']
        
    def __str__(self):
        signo = "+" if self.tipo == TipoMovimiento.INGRESO else "-"
        return f"{self.fecha} | {signo}${self.monto} | {self.categoria.nombre}"
    
    def save(self, *args, **kwargs):
        # Validar que la categoría corresponda al tipo de movimiento
        if self.categoria.tipo != self.tipo:
            raise ValueError(
                f"La categoría '{self.categoria.nombre}' es de tipo "
                f"'{self.categoria.get_tipo_display()}' pero el movimiento "
                f"es de tipo '{self.get_tipo_display()}'"
            )
        super().save(*args, **kwargs)

class SaldoCaja(models.Model):
    """Resumen del saldo de caja por período"""
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    # Saldos calculados
    saldo_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_ingresos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_egresos = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    saldo_final = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Metadatos
    fecha_calculo = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Saldo de Caja"
        verbose_name_plural = "Saldos de Caja"
        ordering = ['-fecha_fin']
        unique_together = ['fecha_inicio', 'fecha_fin']
    
    def __str__(self):
        return f"Saldo {self.fecha_inicio} - {self.fecha_fin}: ${self.saldo_final}"
    
    def calcular_saldo(self):
        """Calcula los totales basado en los movimientos del período"""
        from django.db.models import Sum, Q
        
        # Filtrar movimientos del período
        movimientos = MovimientoCaja.objects.filter(
            fecha__gte=self.fecha_inicio,
            fecha__lte=self.fecha_fin
        )
        
        # Calcular totales
        ingresos = movimientos.filter(
            tipo=TipoMovimiento.INGRESO
        ).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        egresos = movimientos.filter(
            tipo=TipoMovimiento.EGRESO
        ).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0.00')
        
        # Actualizar valores
        self.total_ingresos = ingresos
        self.total_egresos = egresos
        self.saldo_final = self.saldo_inicial + self.total_ingresos - self.total_egresos
        
        return self.saldo_final
