from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, UsernameField, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import *

class PGLoginFormOwner(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )

from django import forms
from .models import Room

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['room_number', 'number_of_beds', 'rent_amount', 'status']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control'}),
            'number_of_beds': forms.NumberInput(attrs={'class': 'form-control'}),
            'rent_amount': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
class TenantForm(forms.ModelForm):
    PROOF_CHOICES = [
        ("Aadhar", "Aadhar"),
        ("PAN Card", "PAN Card"),
        ("Passport", "Passport"),
        ("Driving License", "Driving License"),
        ("Working Company ID", "Working Company ID"),
        ("Other", "Other"),
    ]
    name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=False
    )
    contact_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    proof_name = forms.ChoiceField(
        choices=PROOF_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'proof_name'}),
        required=False
    )
    other_proof_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'proof_other', 'style': 'display:none;'}),
        required=False
    )
    proof_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    check_in_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required= False
    )

    assigned_bed = forms.ModelChoiceField(
        queryset=Bed.objects.filter(is_vacant=False),  # Default empty queryset
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Available Bed",
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)  # Extract request if passed
        super().__init__(*args, **kwargs)
              # Ensure request is valid
        if request:
            pg_id = request.session.get("pg_id")  # Retrieve PG ID from session
            if pg_id:
                try:
                    pg = PG.objects.get(id=pg_id)  # Fetch PG instance
                    pg_name = pg.pg_name
                    self.fields['assigned_bed'].queryset = Bed.objects.filter(pg_name=pg_name, is_vacant=False)
                    # self.fields['assigned_room'].queryset = Room.objects.filter(pg_name=pg_name, status='available')

                except PG.DoesNotExist:
                    return ValidationError("PG not found. Please log in again.")
            else:
                raise ValidationError("You must be logged in to add a tenant.")

    class Meta:
        model = Tenant
        fields = ['name', 'email', 'contact_number', 'assigned_bed', 'check_in_date', 'proof_name', 'other_proof_name', 'proof_number', 'proof_file']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'assigned_room': forms.Select(attrs={'class': 'form-select'}),
            'assigned_bed': forms.Select(attrs={'class': 'form-select'}),
            'check_in_date': forms.DateInput(attrs={'class': 'form-control'}),
            'check_out_date': forms.DateInput(attrs={'class': 'form-control'}),
            'proof_name': forms.TextInput(attrs={'class': 'form-control'}),
            'proof_number': forms.TextInput(attrs={'class': 'form-control'}),
            'proof_file': forms.FileInput(attrs={'class': 'form-control'}),
        } 

class PgOwnerProfileForm(forms.ModelForm):
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control small-textarea'}))
    class Meta:
        model = PG
        fields = ['pg_name', 'name', 'contact_number', 'email', 'address']


class PGLoginFormTenant(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'transaction_id']

from django import forms
from .models import Complaint

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['complaint_text']

#---------------Apartment-------------------------------------------













#--------------------default one-----------------------------------------  -----
class RegistrationForm(UserCreationForm):
  password1 = forms.CharField(
      label=_("Password"),
      widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
  )
  password2 = forms.CharField(
      label=_("Password Confirmation"),
      widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password Confirmation'}),
  )

  class Meta:
    model = User
    fields = ('username', 'email', )

    widgets = {
      'username': forms.TextInput(attrs={
          'class': 'form-control',
          'placeholder': 'Username'
      }),
      'email': forms.EmailInput(attrs={
          'class': 'form-control',
          'placeholder': 'Email'
      })
    }


class LoginForm(AuthenticationForm):
  username = UsernameField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}))
  password = forms.CharField(
      label=_("Password"),
      strip=False,
      widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
  )

class UserPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email'
    }))

class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")
    

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Old Password'
    }), label='Old Password')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")