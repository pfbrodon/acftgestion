from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from socios.models import Socio, Categoria, Concepto, Cuota, SaldoSocio
from decimal import Decimal
from datetime import date

class Command(BaseCommand):
    help = 'Crea datos de ejemplo para probar el sistema de pagos múltiples'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de ejemplo...'))
        
        # Crear categorías si no existen
        categoria_cadete, created = Categoria.objects.get_or_create(
            nombre='Cadete',
            defaults={'descripcion': 'Categoría inicial para nuevos socios'}
        )
        
        categoria_senior, created = Categoria.objects.get_or_create(
            nombre='Senior',
            defaults={'descripcion': 'Categoría para socios senior'}
        )
        
        # Crear conceptos si no existen
        concepto_cuota, created = Concepto.objects.get_or_create(
            nombre='Cuota Social',
            defaults={
                'descripcion': 'Cuota mensual de socio',
                'monto_sugerido': Decimal('5000.00'),
                'activo': True
            }
        )
        
        concepto_cancha, created = Concepto.objects.get_or_create(
            nombre='Uso de Cancha',
            defaults={
                'descripcion': 'Pago por uso de cancha',
                'monto_sugerido': Decimal('3000.00'),
                'activo': True
            }
        )
        
        # Crear cuotas para los últimos 3 meses y próximos 2 meses
        meses_datos = [
            (7, 2025, 'Julio 2025'),
            (8, 2025, 'Agosto 2025'),
            (9, 2025, 'Septiembre 2025'),
            (10, 2025, 'Octubre 2025'),
            (11, 2025, 'Noviembre 2025'),
        ]
        
        for mes, anio, descripcion in meses_datos:
            for concepto in [concepto_cuota, concepto_cancha]:
                cuota, created = Cuota.objects.get_or_create(
                    mes=mes,
                    anio=anio,
                    concepto=concepto,
                    defaults={
                        'monto': concepto.monto_sugerido,
                        'activa': True
                    }
                )
                if created:
                    self.stdout.write(f'Creada cuota: {cuota}')
        
        # Crear usuarios y socios de ejemplo
        socios_ejemplo = [
            {
                'username': 'juan.perez',
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'dni': '12345678',
                'email': 'juan.perez@email.com',
                'celular': '1234567890',
                'categoria': categoria_cadete,
                'saldo_inicial': Decimal('2500.00')  # Saldo a favor
            },
            {
                'username': 'maria.garcia',
                'nombre': 'María',
                'apellido': 'García',
                'dni': '87654321',
                'email': 'maria.garcia@email.com',
                'celular': '0987654321',
                'categoria': categoria_senior,
                'saldo_inicial': Decimal('-1500.00')  # Deuda
            },
            {
                'username': 'carlos.lopez',
                'nombre': 'Carlos',
                'apellido': 'López',
                'dni': '11223344',
                'email': 'carlos.lopez@email.com',
                'celular': '1122334455',
                'categoria': categoria_cadete,
                'saldo_inicial': Decimal('0.00')  # Sin saldo
            }
        ]
        
        for socio_data in socios_ejemplo:
            # Crear usuario si no existe
            user, created = User.objects.get_or_create(
                username=socio_data['username'],
                defaults={
                    'email': socio_data['email'],
                    'first_name': socio_data['nombre'],
                    'last_name': socio_data['apellido']
                }
            )
            
            if created:
                user.set_password('123456')  # Contraseña temporal
                user.save()
            
            # Crear socio si no existe
            socio, created = Socio.objects.get_or_create(
                dni=socio_data['dni'],
                defaults={
                    'usuario': user,
                    'nombre': socio_data['nombre'],
                    'apellido': socio_data['apellido'],
                    'direccion': f'Dirección de {socio_data["nombre"]} {socio_data["apellido"]}',
                    'categoria': socio_data['categoria'],
                    'email': socio_data['email'],
                    'celular': socio_data['celular'],
                    'fecha_nacimiento': date(1990, 1, 1)
                }
            )
            
            if created:
                self.stdout.write(f'Creado socio: {socio}')
                
                # Crear saldo inicial
                saldo_socio, saldo_created = SaldoSocio.objects.get_or_create(
                    socio=socio,
                    defaults={'saldo_actual': socio_data['saldo_inicial']}
                )
                
                if saldo_created and socio_data['saldo_inicial'] != 0:
                    saldo_socio.agregar_saldo(
                        socio_data['saldo_inicial'],
                        f"Saldo inicial del socio {socio.nombre} {socio.apellido}"
                    )
                    # Corregir para que no se duplique
                    saldo_socio.saldo_actual = socio_data['saldo_inicial']
                    saldo_socio.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                'Datos de ejemplo creados exitosamente!\n'
                'Usuarios creados: juan.perez, maria.garcia, carlos.lopez (contraseña: 123456)\n'
                'Puedes probar el sistema de pagos múltiples con estos socios.'
            )
        )
