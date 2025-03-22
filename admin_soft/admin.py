from django.contrib import admin
from .models import Hospital
from django import forms
from django.contrib.auth.hashers import make_password

admin.site.site_header = "Lotez Admin Panel"
admin.site.site_title = "Lotez Admin"
admin.site.index_title = "Welcome to Lotez Administration"

class HospitalAdminForm(forms.ModelForm):
    """Custom form for the Hospital model to ensure password hashing."""
    class Meta:
        model = Hospital
        exclude = ['role']

    def clean_password(self):
        """Hashes the password if it's not already hashed."""
        password = self.cleaned_data['password']
        if not password.startswith('pbkdf2_sha256$'):
            return make_password(password)
        return password

@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    form = HospitalAdminForm
    list_display = ('hospital_name', 'username', 'contact_number', 'email')
    search_fields = ('hospital_name', 'username', 'email')

from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from .models import PG
from .apartmentmodels import Apartment
class ApartmentAdminForm(forms.ModelForm):
    """Custom form for the Apartment model to ensure password hashing."""
    class Meta:
        model = Apartment
        exclude = ['role']

    def clean_password(self):
        """Hashes the password if it's not already hashed."""
        password = self.cleaned_data['password']
        if not password.startswith('pbkdf2_sha256$'):
            return make_password(password)
        return password

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    form = ApartmentAdminForm
    list_display = ('name', 'contact_number', 'email')
    search_fields = ('name', 'email')

class PGAdminForm(forms.ModelForm):
    """Custom form for the PG model to ensure password hashing."""
    class Meta:
        model = PG
        # fields = [f.name for f in PG._meta.fields if f.name != 'role'] or
        exclude = ['role']
    def clean_password(self):
        """Hashes the password if it's not already hashed."""
        password = self.cleaned_data['password']
        if not password.startswith('pbkdf2_sha256$'):
            return make_password(password)
        return password

@admin.register(PG)
class PGAdmin(admin.ModelAdmin):
    form = PGAdminForm
    list_display = ('name', 'contact_number', 'email')
    search_fields = ('name', 'email')
