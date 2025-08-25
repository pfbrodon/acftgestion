
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
    )
    
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name='pagos')
    # Campos antiguos para migración
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name='pagos_antiguos', null=True, blank=True)
    mes_correspondiente = models.CharField(max_length=20, help_text="Mes al que corresponde el pago (ej: Enero 2025)", null=True, blank=True)
    # Nuevo campo
    cuota = models.ForeignKey(Cuota, on_delete=models.PROTECT, related_name='pagos', null=True, blank=True)
    
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField(default=timezone.now)
    metodo_pago = models.CharField(max_length=15, choices=METODO_PAGO_CHOICES, default='efectivo')
    comprobante = models.CharField(max_length=100, blank=True, null=True, help_text="Número de comprobante o referencia")
    comentarios = models.TextField(blank=True, null=True)
    
    def __str__(self):
        if self.cuota:
            return f"Pago {self.cuota} - {self.socio}"
        else:
            # Para pagos antiguos
            concepto_str = f" - {self.concepto}" if self.concepto else ""
            return f"Pago {self.mes_correspondiente}{concepto_str} - {self.socio}"
    
    def save(self, *args, **kwargs):
        # Sincronizar monto con la cuota por defecto si es un pago nuevo
        if not self.pk and self.cuota and not self.monto:
            self.monto = self.cuota.monto
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_pago']