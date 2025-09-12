
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import datetime

class Concepto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    monto_sugerido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} (${self.monto_sugerido})"
    
    class Meta:
        verbose_name = "Concepto"
        verbose_name_plural = "Conceptos"
        ordering = ['nombre']

class Cuota(models.Model):
    """
    Modelo para representar cuotas mensuales.
    El código será: mes (01-12) + año (24, 25, etc.)
    Ejemplo: enero 2024 = 0124, diciembre 2025 = 1225
    """
    codigo = models.CharField(max_length=4, unique=True, help_text="Formato: MMYY (ej: 0124 para enero 2024)")
    mes = models.IntegerField(help_text="Mes (1-12)")
    anio = models.IntegerField(help_text="Año completo (ej: 2024)")
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name='cuotas')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[self.mes]} {self.anio} - {self.concepto.nombre} (${self.monto})"
    
    def save(self, *args, **kwargs):
        # Generar código automáticamente si no existe
        if not self.codigo:
            self.codigo = f"{self.mes:02d}{str(self.anio)[-2:]}"
        # Sincronizar monto con el concepto siempre
        if self.concepto:
            self.monto = self.concepto.monto_sugerido
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Cuota"
        verbose_name_plural = "Cuotas"
        ordering = ['-anio', '-mes']
        unique_together = ['mes', 'anio', 'concepto']

class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Socio(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='socio', null=True, blank=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    direccion = models.CharField(max_length=200)
    dni = models.CharField(max_length=20, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='socios', null=True)
    email = models.EmailField()
    celular = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField()
    fecha_alta = models.DateField(auto_now_add=True)
    # Campo para permisos especiales
    es_administrador = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.dni})"
    
    def get_estado_pagos(self):
        """Retorna el estado de pagos del socio basado en cuotas"""
        hoy = timezone.now().date()
        mes_actual = hoy.month
        anio_actual = hoy.year
        
        # Buscar cuota del mes actual
        try:
            cuota_actual = Cuota.objects.filter(
                mes=mes_actual,
                anio=anio_actual,
                activa=True
            ).first()
            
            if cuota_actual:
                # Verificar si tiene pago para la cuota actual
                pago_mes_actual = self.pagos.filter(cuota=cuota_actual).exists()
                if pago_mes_actual:
                    return "Al día"
        except Cuota.DoesNotExist:
            pass
        
        # Verificar pagos en los últimos 3 meses
        tres_meses_atras = hoy - datetime.timedelta(days=90)
        pagos_recientes = self.pagos.filter(
            fecha_pago__gte=tres_meses_atras
        ).exists()
        
        if pagos_recientes:
            return "Con atraso"
            
        return "Moroso"
    
    class Meta:
        verbose_name = "Socio"
        verbose_name_plural = "Socios"

class Pago(models.Model):
    METODO_PAGO_CHOICES = (
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('debito', 'Débito'),
        ('credito', 'Crédito'),
        ('saldo_favor', 'Saldo a favor'),
    )
    
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name='pagos')
    # Campos antiguos para migración
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name='pagos_antiguos', null=True, blank=True)
    mes_correspondiente = models.CharField(max_length=20, help_text="Mes al que corresponde el pago (ej: Enero 2025)", null=True, blank=True)
    # Nuevo campo - mantener para compatibilidad con pagos únicos
    cuota = models.ForeignKey(Cuota, on_delete=models.PROTECT, related_name='pagos', null=True, blank=True)
    
    # Nuevos campos para pagos múltiples
    es_pago_multiple = models.BooleanField(default=False, help_text="Indica si este pago cubre múltiples cuotas")
    cuotas = models.ManyToManyField(Cuota, through='DetallePago', related_name='pagos_multiples', blank=True)
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    monto_saldo_usado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Monto de saldo a favor usado en este pago"
    )
    monto_sobrante = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Monto sobrante que se agrega al saldo del socio"
    )
    fecha_pago = models.DateField(default=timezone.now)
    metodo_pago = models.CharField(max_length=15, choices=METODO_PAGO_CHOICES, default='efectivo')
    comprobante = models.CharField(max_length=100, blank=True, null=True, help_text="Número de comprobante o referencia")
    comentarios = models.TextField(blank=True, null=True)
    
    def __str__(self):
        if self.es_pago_multiple:
            cuotas_count = self.detalles.count()
            return f"Pago múltiple ({cuotas_count} cuotas) - {self.socio}"
        elif self.cuota:
            return f"Pago {self.cuota} - {self.socio}"
        else:
            # Para pagos antiguos
            concepto_str = f" - {self.concepto}" if self.concepto else ""
            return f"Pago {self.mes_correspondiente}{concepto_str} - {self.socio}"
    
    def get_cuotas_pagadas(self):
        """Retorna las cuotas relacionadas con este pago"""
        if self.es_pago_multiple:
            return [detalle.cuota for detalle in self.detalles.all()]
        elif self.cuota:
            return [self.cuota]
        return []
    
    def get_monto_total_efectivo(self):
        """Retorna el monto total efectivo pagado (sin incluir saldo usado)"""
        return self.monto - self.monto_saldo_usado
    
    def save(self, *args, **kwargs):
        # Sincronizar monto con la cuota por defecto si es un pago nuevo y único
        if not self.pk and self.cuota and not self.monto and not self.es_pago_multiple:
            self.monto = self.cuota.monto
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']

class SaldoSocio(models.Model):
    """Modelo para manejar saldos a favor y en contra de cada socio"""
    socio = models.OneToOneField(Socio, on_delete=models.CASCADE, related_name='saldo')
    saldo_actual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Saldo actual del socio. Positivo = saldo a favor, Negativo = debe"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        signo = "+" if self.saldo_actual >= 0 else ""
        return f"{self.socio} - Saldo: {signo}${self.saldo_actual}"
    
    def agregar_saldo(self, monto, descripcion=""):
        """Agrega monto al saldo (positivo o negativo)"""
        self.saldo_actual += monto
        self.save()
        
        # Registrar el movimiento de saldo
        MovimientoSaldo.objects.create(
            saldo_socio=self,
            monto=monto,
            saldo_anterior=self.saldo_actual - monto,
            saldo_nuevo=self.saldo_actual,
            descripcion=descripcion
        )
    
    class Meta:
        verbose_name = "Saldo de Socio"
        verbose_name_plural = "Saldos de Socios"

class MovimientoSaldo(models.Model):
    """Registro de movimientos en el saldo de los socios"""
    saldo_socio = models.ForeignKey(SaldoSocio, on_delete=models.CASCADE, related_name='movimientos')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    saldo_nuevo = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True)
    pago_relacionado = models.ForeignKey(Pago, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        signo = "+" if self.monto >= 0 else ""
        return f"{self.saldo_socio.socio} - {signo}${self.monto}"
    
    class Meta:
        verbose_name = "Movimiento de Saldo"
        verbose_name_plural = "Movimientos de Saldo"
        ordering = ['-fecha']

class DetallePago(models.Model):
    """Modelo intermedio para relacionar pagos con múltiples cuotas"""
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='detalles')
    cuota = models.ForeignKey(Cuota, on_delete=models.PROTECT)
    monto_aplicado = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Monto del pago aplicado a esta cuota específica"
    )
    monto_restante = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="Monto restante de la cuota después de aplicar el pago"
    )
    pagado_completamente = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.pago} - {self.cuota} (${self.monto_aplicado})"
    
    def save(self, *args, **kwargs):
        # Calcular si la cuota está pagada completamente
        self.monto_restante = self.cuota.monto - self.monto_aplicado
        self.pagado_completamente = self.monto_restante <= 0
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Detalle de Pago"
        verbose_name_plural = "Detalles de Pago"
        unique_together = ['pago', 'cuota']