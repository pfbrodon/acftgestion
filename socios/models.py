
from django.db import models

class Socio(models.Model):
	nombre_apellido = models.CharField(max_length=100)
	direccion = models.CharField(max_length=200)
	dni = models.CharField(max_length=20, unique=True)
	categoria = models.CharField(max_length=50)
	email = models.EmailField()
	celular = models.CharField(max_length=20)
	fecha_nacimiento = models.DateField()
	fecha_alta = models.DateField(auto_now_add=True)

	def __str__(self):
		return f"{self.nombre_apellido} ({self.dni})"
