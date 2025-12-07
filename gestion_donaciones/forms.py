from django import forms
from .models import Donante, ArticuloDonado, Beneficiario, Donacion, Entrega


# 1. Formulario para Donante
class DonanteForm(forms.ModelForm):
    class Meta:
        model = Donante
        fields = [
            'tipoDonante',
            'nombre',
            'apellido',
            'rut',
            'email',
            'telefono',
        ]
        widgets = {
            'tipoDonante': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }


# 2. Formulario para ArticuloDonado
class ArticuloDonadoForm(forms.ModelForm):
    class Meta:
        model = ArticuloDonado
        fields = [
            'nombreObjeto',
            'descripcion',
            'fechaVencimiento',
            'cantidad',
            'categoria',
            'unidad_medida',
        ]
        widgets = {
            'nombreObjeto': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fechaVencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-control'}),
        }


# 3. Formulario para Beneficiario
class BeneficiarioForm(forms.ModelForm):
    class Meta:
        model = Beneficiario
        fields = [
            'nombre',
            'rut',
            'direccion',
            'telefono',
            'email',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


# 4. Formulario para Donacion (cabecera)
class DonacionForm(forms.ModelForm):
    class Meta:
        model = Donacion
        fields = [
            'donante',
            'estado',
            'notas',
        ]
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# 5. Formulario para Entrega (cabecera)
class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = [
            'beneficiario',
            'nombreResponsable',
            'estado',
            'notas',
        ]
        widgets = {
            'nombreResponsable': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
