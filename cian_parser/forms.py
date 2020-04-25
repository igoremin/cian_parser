from django import forms
from .models import ProxyFile
from django.utils.translation import gettext_lazy as _


class ProxyFileForm(forms.ModelForm):
    class Meta:
        model = ProxyFile
        fields = '__all__'

        labels = {
            'proxy_file': _(''),
        }

        field_classes = {
            'proxy_file': forms.CharField,
        }
        widgets = {
            'proxy_file': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

