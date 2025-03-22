from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.core.validators import RegexValidator
from django.utils.timezone import now
import uuid  
import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.signals import post_save
from django.dispatch import receiver

class Apartment(models.Model):  #apartment admin model
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    apartment_name = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=150, unique=True)
    block_name = models.CharField(max_length=150, help_text="Comma-separated names of blocks", default='Block1')
    number_of_blocks = models.PositiveIntegerField(help_text="Total number of blocks in the apartment", default=1)
    contact_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit contact number')]
    )
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    password = models.CharField(max_length=128)  # Secure password storage
    role = models.CharField(max_length=128, default='admin')

    def set_password(self, raw_password):
        """Hashes and stores the password securely using Django's make_password."""
        self.password = make_password(raw_password)
        self.save(update_fields=["password"])

    def check_password(self, raw_password):
        """Checks if the given password matches the stored hash."""
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name


class ApartmentBlock(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='blocks')
    block_name = models.CharField(max_length=150)

    class Meta:
        unique_together = ['apartment', 'block_name']

    def __str__(self):
        return f"{self.apartment.apartment_name} - Block {self.block_name}"

@receiver(post_save, sender=Apartment)
def create_or_update_apartment_blocks(sender, instance, created, **kwargs):
    """Create or update blocks from comma-separated block names when an apartment is created or updated."""
    # Get the block names from the updated apartment instance
    block_names = [name.strip() for name in instance.block_name.split(',') if name.strip()]

    # Fetch existing blocks for this apartment
    existing_blocks = {block.block_name: block for block in instance.blocks.all()}

    # Track blocks that should remain
    updated_blocks = set()

    for block_name in block_names:
        if block_name in existing_blocks:
            # Block already exists, keep it
            updated_blocks.add(block_name)
        else:
            # Create new block
            ApartmentBlock.objects.create(apartment=instance, block_name=block_name)
            updated_blocks.add(block_name)

    # Delete blocks that are no longer in the updated list
    for block in existing_blocks.values():
        if block.block_name not in updated_blocks:
            block.delete()


class ApartmentFlat(models.Model):   #flat owner model
    PURPOSE_CHOICES = [
        ('Rental', 'Rental'),
        ('Owned', 'Owned'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Maintenance', 'Maintenance'),
    ]

    FLAT_TYPES = [
        ('1BHK', '1 BHK'),
        ('2BHK', '2 BHK'),
        ('2.5BHK', '2.5 BHK'),
        ('3BHK', '3 BHK'),
        ('3.5BHK', '3.5 BHK'),
        ('4BHK', '4 BHK'),
        ('Studio', 'Studio'),
    ]

    flat_number = models.CharField(max_length=10)
    block_name = models.ForeignKey('ApartmentBlock', on_delete=models.CASCADE, related_name="flats")  
    flat_type = models.CharField(max_length=10, choices=FLAT_TYPES)
    apartment_name = models.ForeignKey(Apartment, on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=100)
    owner_contact = models.CharField(max_length=15)
    owner_email = models.EmailField()
    flat_size = models.CharField(max_length=10)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Available')
    parking_slots = models.IntegerField(default=1)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default='Rental')
    proof_document_url = models.URLField(max_length=500, blank=True, null=True)  # Store Supabase URL
    password = models.CharField(max_length=255, default='Pavan@123')
    role = models.CharField(max_length=128, default='owner')

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Flat {self.flat_number} - {self.purpose} ({self.status})"
class ApartmentPayment(models.Model):  #payment model
    PAYMENT_MODES = [
        ('CASH', 'Cash'),
        ('ONLINE', 'Online'),
        ('CHEQUE', 'Cheque'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    flat = models.ForeignKey('ApartmentFlat', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    transaction_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODES)
    remarks = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    owner = models.ForeignKey(ApartmentFlat, on_delete=models.CASCADE, related_name='flats')

    def __str__(self):
        return f"Payment of {self.amount} for Flat {self.flat.flat_number} on {self.payment_date} - {self.get_status_display()}"

from django.utils.timezone import now

class ApartmentComplaint(models.Model):
    owner = models.ForeignKey(ApartmentFlat, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(default=now)
    status = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('solved', 'solved')], 
        default='Pending'
    )

    def __str__(self):
        return f"Complaint {self.id} - {self.subject} ({self.status})"


class ApartmentComplaintReply(models.Model):
    complaint = models.ForeignKey(ApartmentComplaint, on_delete=models.CASCADE, related_name='replies')
    sender = models.CharField(max_length=50, choices=[('Owner', 'Owner'), ('Admin', 'Admin')])
    message = models.TextField()
    timestamp = models.DateTimeField(default=now)

    def __str__(self):
        return f"Reply by {self.sender} - {self.timestamp}"
class ApartmentTenant(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    contact_number = models.CharField(max_length=15)
    assigned_owner = models.ForeignKey('ApartmentFlat', on_delete=models.CASCADE)  # Assign flat
    proof_file_url = models.URLField(max_length=500, blank=True, null=True)  # Supabase URL for proof_file
    password = models.CharField(max_length=255, default='Tenant@123')
    role = models.CharField(max_length=128, default='tenant')

    def save(self, *args, **kwargs):
        if not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)  # Encrypt password
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.name} - {self.assigned_owner.flat_number}"
    def __str__(self):
        return f"Reply by {self.sender} - {self.timestamp}"
 
 #----------------------------------------------------------------------------------------------
class ApartmentAnnouncement(models.Model):
    """Stores announcements for an apartment."""
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=now)

    # Attachments & Extras
    image = models.ImageField(upload_to='announcements/images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)  # Supabase URL for image
    file_attachment_url = models.URLField(max_length=500, blank=True, null=True)  # Supabase URL for file
    poll_question = models.ForeignKey('ApartmentAnnouncementPoll', on_delete=models.SET_NULL, blank=True, null=True, related_name='announcements')
    meeting_schedule = models.ForeignKey('ApartmentAnnouncementMeeting', on_delete=models.SET_NULL, blank=True, null=True, related_name='announcements')

    is_completed = models.BooleanField(default=False)  # Indicates if the announcement is completed
    def __str__(self):
        return f"Announcement: {self.title} ({self.created_at.strftime('%d-%m-%Y %H:%M')})"

class ApartmentAnnouncementReply(models.Model):
    """Allows users to reply to an announcement with text, images, polls, or meetings."""
    ROLE_CHOICES = [('Owner', 'Owner'), ('Admin', 'Admin'), ('Tenant', 'Tenant')]

    announcement = models.ForeignKey(ApartmentAnnouncement, on_delete=models.CASCADE, related_name='replies')
    sender = models.CharField(max_length=50)
    sender_role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=now)

    # Attachments & Extras in Replies
    image = models.ImageField(upload_to='replies/images/', blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)  # Supabase URL for image
    file_attachment_url = models.URLField(max_length=500, blank=True, null=True)  # Supabase URL for file
    poll_question = models.ForeignKey('ApartmentAnnouncementPoll', on_delete=models.SET_NULL, blank=True, null=True, related_name='replies')
    meeting_schedule = models.ForeignKey('ApartmentAnnouncementMeeting', on_delete=models.SET_NULL, blank=True, null=True, related_name='replies')

    def __str__(self):
        return f"Reply by {self.sender} - {self.timestamp.strftime('%d-%m-%Y %H:%M')})"

class ApartmentAnnouncementPoll(models.Model):
    """Stores poll questions separately."""
    question = models.CharField(max_length=255)

    def __str__(self):
        return self.question
class ApartmentAnnouncementPollOption(models.Model):
    """Stores poll options related to a poll."""
    poll = models.ForeignKey(ApartmentAnnouncementPoll, on_delete=models.CASCADE, related_name='options')
    option_text = models.CharField(max_length=255)

    def __str__(self):
        return self.option_text

    def vote_percentage(self):
        """Calculates the vote percentage for this option."""
        total_votes = sum(option.votes.aggregate(total=models.Sum('total_votes'))['total'] or 0 for option in self.poll.options.all())
        if total_votes > 0:
            return (self.votes.aggregate(total=models.Sum('total_votes'))['total'] or 0) * 100 / total_votes
        return 0


class ApartmentAnnouncementPollVote(models.Model):
    """Tracks votes from both Admins (Apartment) and Owners (ApartmentFlat)."""
    poll_option = models.ForeignKey(ApartmentAnnouncementPollOption, on_delete=models.CASCADE, related_name="votes")
    admin_voters = models.ManyToManyField(Apartment, related_name="poll_votes", blank=True)
    owner_voters = models.ManyToManyField(ApartmentFlat, related_name="poll_votes", blank=True)
    total_votes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Poll: {self.poll_option.option_text} | Total Votes: {self.total_votes}"

    def add_vote(self, user_type, user):
        """Adds a vote for an admin or owner, ensuring only one vote per user."""
        if user_type == "admin":
            self.admin_voters.clear()  # Remove previous admin votes for this poll
            self.admin_voters.add(user)  # Add the new vote

        elif user_type == "owner":
            self.owner_voters.clear()  # Remove previous owner votes for this poll
            self.owner_voters.add(user)  # Add the new vote

        self.total_votes = self.admin_voters.count() + self.owner_voters.count()
        self.save()

    def remove_vote(self, user_type, user):
        """Removes a vote for an admin or owner."""
        if user_type == "admin":
            self.admin_voters.remove(user)
        elif user_type == "owner":
            self.owner_voters.remove(user)

        self.total_votes = self.admin_voters.count() + self.owner_voters.count()
        self.save()

from django.db import models

class ApartmentAnnouncementMeeting(models.Model):
    """Stores meeting details separately."""
    title = models.CharField(max_length=255)
    agenda = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    is_completed = models.BooleanField(default=False)  # Indicates if the meeting is completed
    final_outcome = models.TextField(blank=True, null=True)  # Stores the meeting outcome

    def __str__(self):
        return f"Meeting: {self.title} on {self.date} at {self.time} - {'Completed' if self.is_completed else 'Pending'}"

# models.py
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class ApartmentVisitor(models.Model):
    PURPOSE_CHOICES = [
        ('Family/Friend', 'Family/Friend'),
        ('Delivery', 'Delivery'),
        ('Maintenance', 'Maintenance'),
        ('Service', 'Service'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    contact_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit contact number')]
    )
    
    block = models.ForeignKey('ApartmentBlock', on_delete=models.CASCADE, related_name='visitors')
    flat = models.ForeignKey('ApartmentFlat', on_delete=models.CASCADE, related_name='visitors')

    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    other_purpose = models.CharField(max_length=100, blank=True, null=True)
    photo = models.URLField(max_length=500, blank=True, null=True)  # Store Supabase Storage URL

    visit_date = models.DateField(default=timezone.now)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    check_in_time = models.DateTimeField(default=timezone.now)
    check_out_time = models.DateTimeField(blank=True, null=True)
    is_checked_out = models.BooleanField(default=False)
    action = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return f"{self.name} - Visiting {self.flat.flat_number} in {self.block.block_name} on {self.visit_date.strftime('%Y-%m-%d')} at {self.check_in_time.strftime('%H:%M')}"
