# forms.py
from django import forms
from .apartmentmodels import *


class ApartmentLoginFormAdmin(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )


class ApartmentFlatFormAdmin(forms.ModelForm):
    proof_document = forms.FileField(required=False, label="Proof Document")
    block_name = forms.ModelChoiceField(
        queryset=ApartmentBlock.objects.none(),
        required=True,
        help_text="Select the block",
        label="Block Name"
    )

    class Meta:
        model = ApartmentFlat
        exclude = ['password', 'apartment_name', 'status', 'proof_document_url']

    def __init__(self, *args, **kwargs):
        apartment = kwargs.pop('apartment', None)  # Get apartment instance
        super().__init__(*args, **kwargs)
        self.fields['flat_size'].label = "Flat Size (sq ft)"

        # Populate block_name choices dynamically if apartment is provided
        if apartment:
            self.fields['block_name'].queryset = ApartmentBlock.objects.filter(apartment=apartment)

class ApartmentFlatLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )



class ApartmentComplaintForm(forms.ModelForm):
    class Meta:
        model = ApartmentComplaint
        fields = ['subject', 'description']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your complaint', 'rows': 4}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs.update({'class': 'form-control'})
        self.fields['description'].widget.attrs.update({'class': 'form-control'})

class ApartmentComplaintReplyForm(forms.ModelForm):
    class Meta:
        model = ApartmentComplaintReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Reply to complaint', 'rows': 3}),
        }



class ApartmentPaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        owner = kwargs.pop('owner', None)  # Get the owner from the view
        super().__init__(*args, **kwargs)
        
        if owner:
            self.fields['flat'].queryset = ApartmentFlat.objects.filter(id=owner)

    class Meta:
        model = ApartmentPayment
        fields = ['flat', 'amount', 'payment_date', 'payment_mode', 'transaction_id', 'remarks']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_mode': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'flat': forms.Select(attrs={'class': 'form-control'}),
        }

class OwnerProfileForm(forms.ModelForm):
    class Meta:
        model = ApartmentFlat
        fields = ['owner_name', 'owner_contact', 'owner_email', 'flat_size']

class ApartmentTenantForm(forms.ModelForm):
    proof_file = forms.FileField(required=False, label="Proof Document")
    
    class Meta:
        model = ApartmentTenant
        fields = ['name', 'email', 'contact_number']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ApartmentAnnouncementForm(forms.ModelForm):
    """Form for creating an announcement with an optional image, poll, and meeting."""

    image = forms.ImageField(required=False, help_text="Optional: Upload an image.")
    file_attachment = forms.FileField(required=False, help_text="Optional: Attach a document.")
    
    # Poll Fields
    poll_question = forms.CharField(required=False, max_length=255, help_text="Optional: Enter a poll question.")
    poll_options = forms.MultipleChoiceField(
        required=False, widget=forms.CheckboxSelectMultiple, help_text="Add multiple poll options."
    )

    # Meeting Fields
    new_meeting_title = forms.CharField(required=False, max_length=255, label="New Meeting Title")
    new_meeting_agenda = forms.CharField(required=False, widget=forms.Textarea, label="New Meeting Agenda")
    # new_meeting_description = forms.CharField(required=False, widget=forms.Textarea, label="New Meeting Description")
    new_meeting_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="New Meeting Date")
    new_meeting_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'type': 'time'}), label="New Meeting Time")

    class Meta:
        model = ApartmentAnnouncement
        fields = ['title', 'message']

    def save(self, commit=True):
        """Custom save method to create a new poll and meeting, linking them to the announcement."""
        instance = super().save(commit=False)

        # Handle Poll Creation
        poll_question = self.cleaned_data.get("poll_question")
        poll_options = self.data.getlist("poll_options[]")  # Get list of poll options

        if poll_question and poll_options:
            poll, created = ApartmentAnnouncementPoll.objects.get_or_create(question=poll_question)
            print(poll_options)
            if created:
                for option_text in poll_options:
                    print(option_text)
                    ApartmentAnnouncementPollOption.objects.create(poll=poll, option_text=option_text.strip())
            instance.poll_question = poll  # Link poll to announcement

        # Handle Meeting Creation
        new_meeting_title = self.cleaned_data.get("new_meeting_title")
        new_meeting_agenda = self.cleaned_data.get("new_meeting_agenda")
        # new_meeting_description = self.cleaned_data.get("new_meeting_description")
        new_meeting_date = self.cleaned_data.get("new_meeting_date")
        new_meeting_time = self.cleaned_data.get("new_meeting_time")

        if all([new_meeting_title, new_meeting_agenda, new_meeting_date, new_meeting_time]):
            meeting = ApartmentAnnouncementMeeting.objects.create(
                title=new_meeting_title,
                agenda=new_meeting_agenda,
                # description=new_meeting_description,
                date=new_meeting_date,
                time=new_meeting_time
            )
            instance.meeting_schedule = meeting  # Store the Meeting ID in `meeting_schedule`

        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many fields

        return instance

class ApartmentAnnouncementReplyForm(forms.ModelForm):
    """Form for replying to an announcement with optional image, file, poll, and meeting."""

    image = forms.ImageField(required=False, help_text="Optional: Upload an image.")
    file_attachment = forms.FileField(required=False, help_text="Optional: Attach a document.")
    poll = forms.ModelChoiceField(
        queryset=ApartmentAnnouncementPoll.objects.all(),
        required=False,
        empty_label="No Poll",
        help_text="Optional: Select a poll response."
    )
    meeting = forms.ModelChoiceField(
        queryset=ApartmentAnnouncementMeeting.objects.all(),
        required=False,
        empty_label="No Meeting",
        help_text="Optional: Schedule a meeting."
    )

    class Meta:
        model = ApartmentAnnouncementReply
        fields = ['message', 'poll', 'meeting']


class ApartmentTenantLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter Password"})
    )

class VisitorForm(forms.ModelForm):
    contact_number = forms.CharField(
        max_length=10,
        validators=[RegexValidator(r'^\d{10}$', 'Enter a valid 10-digit contact number.')],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ApartmentVisitor
        fields = ['name', 'contact_number', 'block', 'flat', 'purpose', 'other_purpose', 'photo'] 
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'block': forms.Select(attrs={'class': 'form-control'}),
            'flat': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.Select(attrs={'class': 'form-control'}),
            'other_purpose': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }