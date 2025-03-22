from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator
import uuid  
class PG(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pg_name = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=150, unique=True)
    contact_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit contact number')]
    )
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=128)  # Secure password storage
    role = models.CharField(max_length=128, default='pg')

    def set_password(self, raw_password):
        """Hashes and stores the password securely using Django's make_password."""
        self.password = make_password(raw_password)
        self.save(update_fields=["password"])

    def check_password(self, raw_password):
        """Checks if the given password matches the stored hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name


class Room(models.Model):
    pg_name = models.CharField(max_length=100)  # PG name without predefined choices
    room_number = models.CharField(max_length=10, unique=True)
    number_of_beds = models.IntegerField()

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Maintenance'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='available')
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    rent_due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.pg_name} - Room {self.room_number} ({self.get_status_display()})"
        
class Bed(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="beds")
    bed_number = models.PositiveIntegerField()
    is_vacant = models.BooleanField(default=False)  # True = occupied, False = empty
    pg_name = models.CharField(max_length=100)
    def __str__(self):
        status = "Occupied" if self.is_vacant else "Vacant"
        return f"Room {self.room.room_number} - Bed {self.bed_number}: {status}"



class Tenant(models.Model):
    pg_name = models.CharField(max_length=100, null=True, blank=True)  # PG name for tenant reference
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    assigned_room = models.OneToOneField('Room', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_bed = models.OneToOneField('Bed', on_delete=models.SET_NULL, null=True, blank=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    payment_amount = models.IntegerField( default=0)  #rent amount
    due_amount = models.IntegerField(default=0)
    advance_amount = models.IntegerField(default=0)
    total_amount_paid = models.IntegerField(default=0)
    proof_name = models.CharField(max_length=255, null=True, blank=True)
    other_proof_name = models.CharField(max_length=255, null=True, blank=True)
    proof_number = models.CharField(max_length=50, null=True, blank=True)
    proof_file = models.FileField(upload_to='tenant_proofs/')
    password = models.CharField(max_length=128)  # Hashed password

    def save(self, *args, **kwargs):
        # Hash password only if it's not already hashed
        if not self.password or self.password == 'Pavan@123' or not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password('Pavan@123')
        super().save(*args, **kwargs)

    def set_password(self, raw_password):
        """Set and hash the password."""
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """Check if the provided password matches the stored hash."""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name if self.name else "Unnamed Tenant"


class Complaint(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='complaints')
    complaint_text = models.TextField()
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Resolved', 'Resolved')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Complaint by {self.tenant.name} - {self.status}"


class Payment(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[('Cash', 'Cash'), ('Online', 'Online'), ('UPI', 'UPI')])
    status = models.CharField(max_length=50, choices=[('Pending', 'Pending'), ('Completed', 'Completed')], default='Pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of ₹{self.amount} by {self.tenant.name} - {self.status}"
















#-----------------------------------------------------------------------------------
class Hospital(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hospital_name = models.CharField(max_length=150, unique=True)
    username = models.CharField(max_length=150, unique=True)
    contact_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit contact number')]
    )
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=128)  # Hashed password storage
    role = models.CharField(max_length=128, default='hospital')

    def set_password(self, raw_password):
        """Hashes and stores the password."""
        self.password = make_password(raw_password)
        self.save()

    def check_password(self, raw_password):
        """Checks if the given password matches the stored hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.hospital_name

#-----------------------------------------------------------------------------------

class Patient(models.Model):
    """
    Model to store patient information.
    """
    name = models.CharField(max_length=255)
    dob = models.DateField()  # Date of Birth for the patient
    contact = models.CharField(max_length=15)
    hospital = models.CharField(max_length=255)  # Hospital name, could be related to a hospital user
    joining_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

from django.views.generic.edit import UpdateView
from .models import Patient

class Doctor(models.Model):
    """
    Model to store doctor information.
    """
    name = models.CharField(max_length=255)
    specialty = models.CharField(max_length=255)
    contact = models.CharField(max_length=15)
    joining_date = models.DateField()  # Joining date for the doctor
    hospital = models.CharField(max_length=255)  # Hospital name, could be related to a hospital user
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name

class Medicine(models.Model):
    """
    Model to store medicine inventory information.
    """
    name = models.CharField(max_length=255)  # Medicine name
    manufacturer = models.CharField(max_length=255)  # Manufacturer name
    quantity = models.PositiveIntegerField()  # Quantity available in stock
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)  # Price per unit of medicine
    hospital = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.name} ({self.batch_number})"
from django.db import models

class UserHospital(models.Model):
    ROLE_CHOICES = [
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('pharmacist', 'Pharmacist'),
        ('other', 'Other Employees'),
    ]

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)  # Use Django's hashing for security
    contact_number = models.CharField(max_length=10)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = models.JSONField()  # Checklist permissions
    hospital = models.CharField(max_length=150, blank=True, null=True)  # Hospital association

    def save(self, *args, **kwargs):
        # Automatically assign hospital to the current user's username if not already set
        if not self.hospital:
            from admin_soft.models import User as AccountsUser
            hospital_user = AccountsUser.objects.filter(role='hospital').first()
            self.hospital = hospital_user.username if hospital_user else None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

#-------------------------------------------------------------------------------

class AvailableSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    interval = models.IntegerField()  # Store interval in minutes
    hospital = models.CharField(max_length=255)
    is_booked = models.BooleanField(default=False)  # ✅ New field to track booking status

    def __str__(self):
        status = "Booked" if self.is_booked else "Available"
        return f"{self.doctor.name} | {self.date} | {self.start_time} - {self.end_time} | {status}"

from django.db import models

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Canceled', 'Canceled'),
        ('Completed', 'Completed'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    slot = models.ForeignKey(AvailableSlot, on_delete=models.CASCADE)
    reason = models.TextField()
    hospital = models.CharField(max_length=255)  # Hospital name, could be related to a hospital user
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Scheduled',  # Default value set to 'Scheduled'
    )

    def __str__(self):
        return f'Appointment with {self.doctor.name} on {self.date} at {self.slot.start_time}'

#-----------------------------------------------------------------------------------


