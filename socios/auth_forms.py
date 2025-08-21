from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Socio, Categoria

class RegistroUsuarioForm(UserCreationForm):
    # Campos para el modelo User
    username = forms.CharField(label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    # Campos para el modelo Socio
    nombre = forms.CharField(label='Nombre', widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellido = forms.CharField(label='Apellido', widget=forms.TextInput(attrs={'class': 'form-control'}))
    direccion = forms.CharField(label='Dirección', widget=forms.TextInput(attrs={'class': 'form-control'}))
    dni = forms.CharField(label='DNI', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    celular = forms.CharField(label='Celular', widget=forms.TextInput(attrs={'class': 'form-control'}))
    fecha_nacimiento = forms.DateField(
        label='Fecha de nacimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'lang': 'es'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            
            # Buscar la categoría "Cadete" o crear si no existe
            categoria_cadete, created = Categoria.objects.get_or_create(
                nombre='Cadete',
                defaults={'descripcion': 'Categoría inicial para nuevos socios'}
            )
            
            # Crear el perfil de socio asociado al usuario
            Socio.objects.create(
                usuario=user,
                nombre=self.cleaned_data['nombre'],
                apellido=self.cleaned_data['apellido'],
                direccion=self.cleaned_data['direccion'],
                dni=self.cleaned_data['dni'],
                categoria=categoria_cadete,
                email=self.cleaned_data['email'],
                celular=self.cleaned_data['celular'],
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento']
            )
        
        return user

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
