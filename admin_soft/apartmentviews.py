from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.views import *
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from admin_soft.forms import *
from .apartmentmodels import *
from django.utils import timezone
from datetime import date
from .apartmentforms import *
from django.views.generic import DetailView
from django.urls import reverse
from django.db.models import Sum
from django.http import JsonResponse
import json
from datetime import datetime
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
import base64
import uuid
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
import random
from django.core.cache import cache
import requests
import urllib.request
from .supabase_config import supabase, BUCKET_NAME, upload_file

class ApartmentLoginViewAdmin(View):
    template_name = 'apartment/admin/apartment_admin_login.html'
    form_class = ApartmentLoginFormAdmin

    def get(self, request, *args, **kwargs):
        """If already logged in, redirect to dashboard."""
        if request.session.get("apartment_id"):  # Check if apartment admin is logged in
            return redirect("apartment_admin_dashboard")
        
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """Handle login authentication."""
        if request.session.get("apartment_id"):  # If already logged in, redirect to dashboard
            return redirect("apartment_admin_dashboard")

        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            try:
                apartment = Apartment.objects.get(name=username)
                if check_password(password, apartment.password):
                    # Convert UUID to string before storing in session
                    request.session["apartment_id"] = str(apartment.id)
                    request.session["apartment_name"] = apartment.apartment_name
                    messages.success(request, "Login successful.")
                    return redirect("apartment_admin_dashboard")
                else:
                    messages.error(request, "Invalid password.")
            except Apartment.DoesNotExist:
                messages.error(request, "Apartment admin does not exist.")

        return render(request, self.template_name, {"form": form})

def apartment_admin_dashboard(request):
    """Apartment admin dashboard view."""
    if not request.session.get("apartment_id"):  # Check if apartment admin is logged in
        return redirect("apartment_admin_login")
    apartment_id = request.session.get("apartment_id")
    apartment = Apartment.objects.get(id=apartment_id)
    return render(request, 'apartment/admin/apartment_admin_dashboard.html', {"apartment": apartment})
def apartment_admin_profile(request):
    admin_id = request.session.get('apartment_id')
    if not admin_id:
        messages.error(request, "You must be logged in to view the profile.")
        return redirect('apartment_admin_login')  # Redirect to login if not authenticated

    admin = Apartment.objects.get(id=admin_id)  # Get logged-in admin details
    return render(request, 'apartment/admin/apartment_admin_profile.html', {'admin': admin})

def apartment_admin_logout(request):
    """Apartment admin logout view."""
    print("hai")
    logout(request)
    return redirect("apartment_admin_login")
 



def list_flats(request):
    apartment_id = request.session.get("apartment_id")
    apartment = Apartment.objects.get(id=apartment_id)
    flats = ApartmentFlat.objects.filter(apartment_name=apartment)
    return render(request, 'apartment/admin/flat/apartment_flat_dashboard.html', {'flats': flats, 'apartment': apartment})

def add_flat(request):
    apartment_id = request.session.get("apartment_id")
    apartment = get_object_or_404(Apartment, id=apartment_id)

    if request.method == 'POST':
        form = ApartmentFlatFormAdmin(request.POST, request.FILES, apartment=apartment)
        if form.is_valid():
            flat = form.save(commit=False)
            flat.apartment_name = apartment  # Assign the apartment

            # Validate block selection
            block = form.cleaned_data['block_name']
            if not ApartmentBlock.objects.filter(apartment=apartment, id=block.id).exists():
                messages.error(request, "Invalid block selection.")
                return render(request, 'apartment/admin/flat/apartment_flat_add.html', {'form': form, 'apartment': apartment})

            # Handle file upload
            if 'proof_document' in request.FILES:
                file = request.FILES['proof_document']
                file_url = upload_file(file, 'flat_proofs')  # Function to upload to storage
                if file_url:
                    flat.proof_document_url = file_url
                else:
                    messages.error(request, "Error uploading proof document")
                    return render(request, 'apartment/admin/flat/apartment_flat_add.html', {'form': form, 'apartment': apartment})

            flat.save()
            messages.success(request, "Flat added successfully!")
            return redirect('list_flats')
    else:
        form = ApartmentFlatFormAdmin(apartment=apartment)

    return render(request, 'apartment/admin/flat/apartment_flat_add.html', {'form': form, 'apartment': apartment})

class ApartmentFlatDetailView(DetailView):
    model = ApartmentFlat
    template_name = 'apartment/admin/flat/apartment_flat_detail.html'
    context_object_name = 'flat'

def edit_flat(request, pk):
    flat = get_object_or_404(ApartmentFlat, pk=pk)
    if request.method == 'POST':
        form = ApartmentFlatFormAdmin(request.POST, request.FILES, instance=flat)
        if form.is_valid():
            flat = form.save(commit=False)
            
            # Validate block name against apartment's blocks
            block_name = form.cleaned_data['block_name']
            apartment = flat.apartment_name
            if block_name.upper() not in [chr(65 + i) for i in range(apartment.number_of_blocks)]:
                messages.error(request, f"Invalid block name. Please choose from blocks A to {chr(64 + apartment.number_of_blocks)}")
                return render(request, 'apartment/admin/flat/apartment_flat_edit.html', {'form': form, 'flat': flat})
            
            # Handle file upload to Supabase
            if 'proof_document' in request.FILES:
                file = request.FILES['proof_document']
                file_url = upload_file(file, 'flat_proofs')
                if file_url:
                    flat.proof_document_url = file_url
                else:
                    messages.error(request, "Error uploading proof document")
                    return render(request, 'apartment/admin/flat/apartment_flat_edit.html', {'form': form, 'flat': flat})
            
            flat.save()
            messages.success(request, "Flat updated successfully!")
            return redirect('list_flats')
    else:
        form = ApartmentFlatFormAdmin(instance=flat)
    return render(request, 'apartment/admin/flat/apartment_flat_edit.html', {'form': form, 'flat': flat})

def delete_flat(request, pk):
    flat = get_object_or_404(ApartmentFlat, pk=pk)
    if request.method == 'POST':
        flat.delete()
        return redirect('list_flats')
    return render(request, 'apartment/admin/flat/apartment_flat_delete.html', {'flat': flat})

def list_payments(request):
    apartment_id = request.session.get("apartment_id")
    print(apartment_id)
    payments = ApartmentPayment.objects.filter(owner__apartment_name_id=apartment_id).order_by('-payment_date')

    # Get the current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Handle the 'search' filter: searches transaction_id, remarks, and flat number.
    search_query = request.GET.get('search', '').strip()
    if search_query:
        payments = payments.filter(
            Q(transaction_id__icontains=search_query) |
            Q(remarks__icontains=search_query) |
            Q(flat__flat_number__icontains=search_query)
        )

    # Handle the 'status' filter.
    status = request.GET.get('status', '').strip()
    if status:
        payments = payments.filter(status=status)

    # Handle the 'month' filter (default: current month)
    month = request.GET.get('month', '').strip()
    if not month or not month.isdigit():  # Default to current month if not provided
        month = str(current_month)
    payments = payments.filter(payment_date__month=int(month))

    # Handle the 'year' filter (default: current year)
    year = request.GET.get('year', '').strip()
    if not year or not year.isdigit():  # Default to current year if not provided
        year = str(current_year)
    payments = payments.filter(payment_date__year=int(year))

    # Generate the list of years from 2024 to the current year.
    years = range(2024, current_year + 1)

    # Dictionary of months for dropdown
    months = {
        "1": "January", "2": "February", "3": "March",
        "4": "April", "5": "May", "6": "June",
        "7": "July", "8": "August", "9": "September",
        "10": "October", "11": "November", "12": "December"
    }

    context = {
        'payments': payments.order_by('-payment_date'),
        'years': years,
        'months': months,
        'selected_month': month,
        'selected_year': year,
    }

    # For AJAX requests, return only the payments table partial.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'apartment/admin/payment/partials/payments_table.html', context)

    return render(request, 'apartment/admin/payment/apartment_admin_payment.html', context)

def update_payment_status(request):
    payment_id = request.POST.get('payment_id')
    new_status = request.POST.get('status')
    remarks = request.POST.get('remarks', '')

    payment = get_object_or_404(ApartmentPayment, pk=payment_id)
    payment.status = new_status
    payment.remarks = remarks
    payment.save()
    
    return redirect('apartment_payments')




def apartment_flat_login(request):
    """Handles apartment owner login."""
    if request.session.get("owner_id"):
        return redirect("apartment_flat_dashboard") 
    if request.method == "POST":
        form = ApartmentFlatLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            try:
                owner = ApartmentFlat.objects.get(owner_name=username)
                if check_password(password, owner.password):
                    request.session["owner_id"] = owner.id
                    messages.success(request, "Login successful!")
                    return redirect("apartment_flat_dashboard")
                else:
                    messages.error(request, "Invalid password.")
            except ApartmentFlat.DoesNotExist:
                messages.error(request, "Owner not found.")
                form = ApartmentFlatLoginForm()
                return render(request, "apartment/owner/flat_login.html", {"form": form})

    else:
        form = ApartmentFlatLoginForm()

    return render(request, "apartment/owner/flat_login.html", {"form": form})

def apartment_flat_logout(request):
    """Handles apartment owner logout."""
    request.session.flush()
    messages.success(request, "Logged out successfully!")
    return redirect("apartment_flat_login")

def apartment_flat_dashboard(request):
    """Owner's dashboard after login."""
    if not request.session.get("owner_id"):
        messages.error(request, "You must be logged in to access this page.")
        return redirect("apartment_flat_login")
    return render(request, "apartment/owner/flat_dashboard.html")


def apartment_flat_complaints(request):
    """Handles complaint creation and listing for apartment owners."""
    owner_id = request.session.get("owner_id")
    if not owner_id:
        messages.error(request, "You must be logged in to access this page.")
        return redirect("apartment_flat_login")

    owner = get_object_or_404(ApartmentFlat, id=owner_id)
    complaints = ApartmentComplaint.objects.filter(owner=owner).order_by("-created_at")

    if request.method == "POST":
        form = ApartmentComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.owner = owner
            complaint.save()
            messages.success(request, "Complaint submitted successfully.")
            return redirect("apartment_flat_complaints")
        else:
            messages.error(request, "There was an error submitting the complaint.")
    else:
        form = ApartmentComplaintForm()

    return render(request, "apartment/owner/complaint/complaints.html", {"form": form, "complaints": complaints})



def apartment_flat_complaint_replies(request, complaint_id):
    """View and reply to complaints for an owner."""
    
    owner_id = request.session.get("owner_id")
    if not owner_id:
        messages.error(request, "You must be logged in to access this page.")
        return redirect("apartment_flat_login")

    complaint = get_object_or_404(ApartmentComplaint, id=complaint_id, owner_id=owner_id)
    replies = complaint.replies.all()
    owner = ApartmentFlat.objects.get(id=owner_id)

    if request.method == "POST":
        message = request.POST.get("message")
        if message:
            ApartmentComplaintReply.objects.create(
                complaint=complaint,
                sender=owner.owner_name, # Ensure the role is set for filtering
                message=message,
            )
            messages.success(request, "Your reply has been posted.")
            return redirect("apartment_flat_complaint_replies", complaint_id=complaint.id)

    return render(
        request,
        "apartment/owner/complaint/complaint_replies.html",
        {"complaint": complaint, "replies": replies},
    )


def admin_complaint_list(request):
    """Admin Complaint List with Filters."""
    apartment_id = request.session.get("apartment_id")
  
    complaints = ApartmentComplaint.objects.filter(owner__apartment_name_id=apartment_id).order_by('-created_at')
    
    owners = ApartmentFlat.objects.all()  # Get all owners for dropdown
    STATUS_CHOICES = ApartmentComplaint._meta.get_field("status").choices
    # Filtering based on user input
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")
    owner_filter = request.GET.get("owner", "")

    if search_query:
        complaints = complaints.filter(subject__icontains=search_query)

    if status_filter:
        complaints = complaints.filter(status=status_filter)

    if owner_filter:
        complaints = complaints.filter(owner_id=owner_filter)

    return render(
        request,
        "apartment/admin/complaint/complaint_list.html",
        {"complaints": complaints, "owners": owners, "status_choices": STATUS_CHOICES},
    )

def admin_complaint_reply(request, complaint_id):
    """Admin can view and reply to complaints."""
    complaint = get_object_or_404(ApartmentComplaint, id=complaint_id)
    apartment_id = request.session.get("apartment_id")
    apartment = Apartment.objects.get(id=apartment_id)

    if not apartment_id:
        messages.error(request, "You must be logged in as an admin to access this page.")
        return redirect("apartment_admin_login")

    apartment = Apartment.objects.get(id=apartment_id)

    # Fetch all replies related to this complaint
    replies = ApartmentComplaintReply.objects.filter(complaint=complaint).order_by("timestamp")

    if request.method == "POST":
        form = ApartmentComplaintReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.complaint = complaint
            reply.sender = apartment.name  # Ensure sender is properly stored
            # reply.role = "Admin"  # Assign role explicitly
            reply.save()
            messages.success(request, "Reply sent successfully.")
            return redirect("apartment_admin_complaint_reply", complaint_id=complaint.id)
        else:
            messages.error(request, "There was an error sending the reply.")
    else:
        form = ApartmentComplaintReplyForm()

    return render(
        request,
        "apartment/admin/complaint/complaint_reply.html",
        {"form": form, "complaint": complaint, "replies": replies},
    )

def apartment_mark_complaint_solved(request, complaint_id):
    """Marks the complaint as solved."""
    complaint = get_object_or_404(ApartmentComplaint, id=complaint_id)
    complaint.status = 'solved'
    complaint.save()
    messages.success(request, "Complaint marked as solved!")
    return redirect("apartment_flat_complaints") 



def make_payment(request):
    owner_id = request.session.get("owner_id")
    if request.method == "POST":
        form = ApartmentPaymentForm(request.POST)
        print('hai')
        if form.is_valid():
            payment = form.save(commit=False)
            print("hai fin")
            # payment.flat_id = request.session.get("owner_id")
            payment.owner_id = owner_id
            payment.save()
            print('saving')
            messages.success(request, "Payment submitted successfully!")
            return redirect("owner_payments_view")
    else:

        form = ApartmentPaymentForm(owner=owner_id)
    return render(request, "apartment/owner/payment/make_payment.html", {"form": form})


def view_payments(request):
    owner_id= request.session.get("owner_id")
    flat = ApartmentFlat.objects.get(id=owner_id)
    payments = ApartmentPayment.objects.filter(owner_id=owner_id)  # Assuming `owner` is linked to `User`
    return render(request, "apartment/owner/payment/view_payments.html", {"payments": payments})

def flat_owner_profile(request):
    owner_id = request.session.get("owner_id")
    owner = ApartmentFlat.objects.get(id=owner_id)
    return render(request, 'apartment/owner/profile.html', {'owner': owner})

def flat_edit_owner_profile(request):
    owner_id = request.session.get("owner_id")
    owner = ApartmentFlat.objects.get(id=owner_id)  # Assuming email authentication
    if request.method == 'POST':
        form = OwnerProfileForm(request.POST, instance=owner)
        if form.is_valid():
            form.save()
            return redirect('flat_owner_profile')  # Redirect to profile after saving
    else:
        form = OwnerProfileForm(instance=owner)
    
    return render(request, 'apartment/owner/edit_profile.html', {'form': form})


def owner_add_tenant(request):
    if request.method == 'POST':
        form = ApartmentTenantForm(request.POST, request.FILES)
        if form.is_valid():
            tenant = form.save(commit=False)
            tenant.assigned_owner_id = request.session.get("owner_id")
            
            # Handle file upload to Supabase
            if 'proof_file' in request.FILES:
                file = request.FILES['proof_file']
                file_url = upload_file(file, 'tenant_proofs')
                if file_url:
                    tenant.proof_file_url = file_url
                else:
                    messages.error(request, "Error uploading proof document")
                    return render(request, 'apartment/owner/tenant/add_tenant.html', {'form': form})
            
            tenant.save()
            messages.success(request, "Tenant added successfully!")
            return redirect('owner_view_tenant')  # Redirect to Tenant list page
    else:
        form = ApartmentTenantForm()

    return render(request, 'apartment/owner/tenant/add_tenant.html', {'form': form})


def owner_view_tenant(request):
    owner_id = request.session.get("owner_id")
    owner = ApartmentFlat.objects.get(id=owner_id)
    tenants = ApartmentTenant.objects.filter(assigned_owner=owner)
    return render(request, 'apartment/owner/tenant/tenant_list.html', {'tenants': tenants})



def admin_view_tenants(request):
    # Get the logged-in admin's apartment
    admin_apartment_id = request.session.get("apartment_id")
    
    # Get all flats under the admin's apartment
    flats = ApartmentFlat.objects.filter(apartment_name_id=admin_apartment_id)
    
    # Get all tenants in those flats
    tenants = ApartmentTenant.objects.filter(assigned_owner__in=flats)

    return render(request, 'apartment/admin/tenant/tenant_list.html', {'tenants': tenants})


# ------------------ ANNOUNCEMENT CONVERSATION (Replies) ------------------ #

def owner_announcements(request):
    owner_id= request.session.get("owner_id")
    owner = ApartmentFlat.objects.get(id=owner_id)
    announcements = ApartmentAnnouncement.objects.filter(apartment_id=owner.apartment_name_id).order_by('-created_at')
    print("hai")
    return render(request, 'apartment/owner/announcement/announcement_list.html', {'announcements': announcements})
def list_announcements(request):
    apartment_id = request.session.get("apartment_id")
    announcements = ApartmentAnnouncement.objects.filter(apartment_id=apartment_id).order_by('-created_at')
    
    return render(request, 'apartment/admin/announcement/announcement_list.html', {'announcements': announcements})
#------------------------------------------

def send_announcement(request):
    """Handles the creation of an announcement with optional attachments, polls, and meetings."""
    apartment_id = request.session.get("apartment_id")
    apartment = get_object_or_404(Apartment, id=apartment_id)

    if request.method == "POST":
        form = ApartmentAnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.apartment = apartment
            
            # Handle image upload to Supabase
            if 'image' in request.FILES:
                file = request.FILES['image']
                file_url = upload_file(file, 'announcements/images')
                if file_url:
                    announcement.image_url = file_url
            
            # Handle file attachment upload to Supabase
            if 'file_attachment' in request.FILES:
                file = request.FILES['file_attachment']
                file_url = upload_file(file, 'announcements/files')
                if file_url:
                    announcement.file_attachment_url = file_url
            
            announcement.save()
            messages.success(request, "Announcement sent successfully!")
            return redirect('list_announcements')
        messages.error(request, "Error in submitting announcement. Please check your inputs.")
    else:
        form = ApartmentAnnouncementForm()

    return render(request, "apartment/admin/announcement/announcement_send.html", {"form": form, "apartment": apartment})

def admin_announcement_conversation(request, announcement_id):
    """Handles viewing and replying to an announcement conversation (Admin)."""
    apartment_id = request.session.get("apartment_id")
    if not apartment_id:
        messages.error(request, "You must be logged in as an admin to access this page.")
        return redirect("apartment_admin_login")

    apartment = get_object_or_404(Apartment, id=apartment_id)
    announcement = get_object_or_404(
        ApartmentAnnouncement.objects.select_related("apartment"),
        id=announcement_id,
        apartment=apartment
    )
    
    replies = announcement.replies.select_related("announcement").order_by("timestamp")

    if request.method == "POST":
        form = ApartmentAnnouncementReplyForm(request.POST, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.announcement = announcement
            reply.sender = apartment.name
            reply.sender_role = "Admin"
            
            # Handle image upload to Supabase
            if 'image' in request.FILES:
                file = request.FILES['image']
                file_url = upload_file(file, 'replies/images')
                if file_url:
                    reply.image_url = file_url
            
            # Handle file attachment upload to Supabase
            if 'file_attachment' in request.FILES:
                file = request.FILES['file_attachment']
                file_url = upload_file(file, 'replies/files')
                if file_url:
                    reply.file_attachment_url = file_url
                    
            reply.save()
            messages.success(request, "Your reply has been posted.")
            return redirect("admin_announcement_conversation", announcement_id=announcement.id)
    else:
        form = ApartmentAnnouncementReplyForm()

    # Get poll question and its options with votes
    poll = announcement.poll_question
    poll_options = poll.options.all() if poll else None
    total_votes = ApartmentAnnouncementPollVote.objects.filter(poll_option__poll=poll).aggregate(Sum('total_votes'))['total_votes__sum'] or 0

    # Fetch voter names
    voters = []
    if poll_options:
        for option in poll_options:
            for vote in option.votes.all():
                voters.extend(list(vote.admin_voters.values_list('apartment_name', flat=True)))
                voters.extend(list(vote.owner_voters.values_list('owner_name', flat=True)))

    return render(
        request,
        "apartment/admin/announcement/announcement_conversation.html",
        {
            "announcement": announcement,
            "replies": replies,
            "form": form,
            "poll": poll,
            "poll_options": poll_options,
            "total_votes": total_votes,
            "voters": voters,  # <-- Pass the voter list
        },
    )

def admin_vote_poll(request, poll_id):
    """Handles voting for a poll in an announcement (Admin)."""
    if request.method == "POST":
        selected_option_id = request.POST.get("poll_option")

        if not selected_option_id:
            messages.error(request, "Please select an option before voting.")
            return redirect("admin_announcement_conversation", poll_id=poll_id)

        poll_option = get_object_or_404(ApartmentAnnouncementPollOption, id=selected_option_id)

        # Ensure admin is logged in
        apartment_id = request.session.get("apartment_id")
        if not apartment_id:
            messages.error(request, "You must be logged in as an admin to vote.")
            return redirect("apartment_admin_login")

        admin = get_object_or_404(Apartment, id=apartment_id)

        # Remove admin's previous vote in the same poll
        existing_votes = ApartmentAnnouncementPollVote.objects.filter(poll_option__poll=poll_option.poll, admin_voters=admin)
        for vote in existing_votes:
            vote.admin_voters.remove(admin)  # Remove admin from previous votes
            vote.total_votes = vote.admin_voters.count() + vote.owner_voters.count()
            vote.save()

        # Cast a new vote
        poll_vote, created = ApartmentAnnouncementPollVote.objects.get_or_create(poll_option=poll_option)
        poll_vote.admin_voters.add(admin)
        poll_vote.total_votes = poll_vote.admin_voters.count() + poll_vote.owner_voters.count()
        poll_vote.save()

        messages.success(request, "Your vote has been recorded successfully.")
        return redirect(request.META.get('HTTP_REFERER', 'list_announcements'))
    return redirect(request.META.get('HTTP_REFERER', 'list_announcements'))


def owner_vote_poll(request, poll_id):
    """Handles voting on polls."""
    if request.method == "POST":
        option_id = request.POST.get("poll_option")
        owner_id = request.session.get("owner_id")

        if not owner_id:
            messages.error(request, "You must be logged in as an owner to vote.")
            return redirect("apartment_owner_login")

        owner = ApartmentFlat.objects.get(id=owner_id)
        option = get_object_or_404(ApartmentAnnouncementPollOption, id=option_id)

        # Find existing vote for this owner and remove it before adding a new one
        existing_votes = ApartmentAnnouncementPollVote.objects.filter(owner_voters=owner, poll_option__poll=option.poll)
        for vote in existing_votes:
            vote.owner_voters.remove(owner)
            vote.total_votes = vote.admin_voters.count() + vote.owner_voters.count()
            vote.save()

        # Add the new vote
        vote, created = ApartmentAnnouncementPollVote.objects.get_or_create(poll_option=option)
        vote.owner_voters.add(owner)
        vote.total_votes = vote.admin_voters.count() + vote.owner_voters.count()
        vote.save()

        messages.success(request, "Your vote has been recorded.")
        return redirect(request.META.get('HTTP_REFERER', 'owner_announcements'))

def owner_announcement_conversation(request, announcement_id):
    """Handles viewing and replying to an announcement conversation (Owner)."""
    owner_id = request.session.get("owner_id")
    if not owner_id:
        messages.error(request, "You must be logged in as an owner to access this page.")
        return redirect("apartment_owner_login")

    owner = get_object_or_404(ApartmentFlat, id=owner_id)
    announcement = get_object_or_404(
        ApartmentAnnouncement.objects.select_related("apartment"),
        id=announcement_id,
        apartment=owner.apartment_name
    )
    if request.method == "POST":
        form = ApartmentAnnouncementReplyForm(request.POST, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.announcement = announcement
            reply.sender = owner.owner_name
            reply.sender_role = "Owner"
            
            # Handle image upload to Supabase
            if 'image' in request.FILES:
                file = request.FILES['image']
                file_url = upload_file(file, 'replies/images')
                if file_url:
                    reply.image_url = file_url
            
            # Handle file attachment upload to Supabase
            if 'file_attachment' in request.FILES:
                file = request.FILES['file_attachment']
                file_url = upload_file(file, 'replies/files')
                if file_url:
                    reply.file_attachment_url = file_url
            
            reply.save()
            messages.success(request, "Your reply has been posted.")
            return redirect("owner_announcement_conversation", announcement_id=announcement.id)
    else:
        form = ApartmentAnnouncementReplyForm()

    replies = announcement.replies.select_related("announcement").order_by("timestamp")

    # Get poll question and its options with votes
    poll = announcement.poll_question
    poll_options = poll.options.all() if poll else None
    total_votes = ApartmentAnnouncementPollVote.objects.filter(poll_option__poll=poll).aggregate(Sum('total_votes'))['total_votes__sum'] or 0

    # Fetch voter names
    voters = []
    if poll_options:
        for option in poll_options:
            for vote in option.votes.all():
                voters.extend(list(vote.admin_voters.values_list('apartment_name', flat=True)))
                voters.extend(list(vote.owner_voters.values_list('owner_name', flat=True)))

    return render(
        request,
        "apartment/owner/announcement/announcement_conversation.html",
        {
            "announcement": announcement,
            "replies": replies,
            "poll": poll,
            "poll_options": poll_options,
            "total_votes": total_votes,
            "voters": voters,  # <-- Pass the voter list
            "form": form,
        },
    )

def mark_announcement_completed(request):
    """Marks an announcement as completed and updates meeting outcome if required."""
    if request.method == "POST":
        data = json.loads(request.body)
        announcement_id = data.get("announcement_id")
        final_outcome = data.get("final_outcome", "")

        try:
            announcement = get_object_or_404(ApartmentAnnouncement, id=announcement_id)
            announcement.is_completed = True
            announcement.save()

            # If there's a linked meeting, update the final outcome
            if (announcement.meeting_schedule):
                meeting = announcement.meeting_schedule
                meeting.is_completed = True
                meeting.final_outcome = final_outcome
                meeting.save()

            return JsonResponse({"status": "success"})
        except ApartmentAnnouncement.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Announcement not found"}, status=404)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)




#--------------tenant-------------------
def apartment_tenant_login(request):
    """Handles tenant login."""
    if request.method == "POST":
        form = ApartmentTenantLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            print('valid form')
            try:
                tenant = ApartmentTenant.objects.get(name=username)  # Use email for login
                print('valid form')
                if check_password(password, tenant.password):  # Check hashed password
                    request.session["tenant_id"] = tenant.id  # Store tenant ID in session
                    messages.success(request, "Login successful!")
                    return redirect("apartment_tenant_dashboard")  # Redirect to tenant dashboard
                else:
                    messages.error(request, "Invalid password.")
            except Tenant.DoesNotExist:
                messages.error(request, "Tenant not found.")

    else:
        form = ApartmentTenantLoginForm()

    return render(request, "apartment/tenant/apartment_tenant_login.html", {"form": form})


def apartment_tenant_logout(request):
    """Handles tenant logout."""
    request.session.flush()
    messages.success(request, "Logged out successfully!")
    return redirect("apartment_tenant_login")

def apartment_tenant_dashboard(request):
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        return redirect("apartment_tenant_login")
    tenant = ApartmentTenant.objects.get(id=tenant_id)
    return render(request, "apartment/tenant/apartment_tenant_dashboard.html",{"tenant": tenant})

#-----------------------------------------------------------------------------------

# def visitor_registration(request):
#     if request.method == "POST":
#         form_data = request.POST.copy()
#         form_files = request.FILES.copy()
#         photo_data = request.POST.get('photo_data', '')
        
#         # Check if OTP is verified
#         if not request.session.get('otp_verified'):
#             messages.error(request, "Please verify your phone number first.")
#             return JsonResponse({'error': 'OTP verification required'}, status=400)
        
#         form = ApartmentVisitorForm(form_data, form_files)
        
#         if form.is_valid():
#             visitor = form.save(commit=False)
#             visitor.check_in_time = timezone.now()
#             visitor.visit_date = date.today()
            
#             if photo_data and photo_data.startswith('data:image'):
#                 format, imgstr = photo_data.split(';base64,')
#                 ext = format.split('/')[-1]
#                 filename = f"{uuid.uuid4()}.{ext}"
#                 data = base64.b64decode(imgstr)
#                 file_content = ContentFile(data, name=filename)
#                 visitor.photo = file_content
            
#             visitor.save()
            
#             # Clear verification status after successful registration
#             request.session.pop('otp_verified', None)
#             request.session.pop('verified_phone', None)
#             request.session.pop('visitor_form_data', None)
            
#             messages.success(request, "Visitor registered successfully!")
#             return redirect('visitor_registration')
#     else:
#         form = ApartmentVisitorForm()
   
#     flats = ApartmentFlat.objects.all()
#     return render(request, 'apartment/visitor/visitor_registration.html', {'form': form, 'flats': flats})


def owner_view_visitor_list(request):
    """View for apartment owners to see and approve visitors."""
    # Get the flats owned by the logged-in owner
    owner_id= request.session.get("owner_id")
    # Get visitors for those flats
    visitors = ApartmentVisitor.objects.filter(flat_id=owner_id)

    return render(request, 'apartment/owner/visitor/owner_view_visitor.html', {'visitors': visitors})

def visitor_success(request):
    return render(request, 'apartment/visitor/visitor_success.html')

def visitor_registration(request, apartment_id):
    # Render the index page
   
    flat_numbers = ApartmentFlat.objects.filter(apartment_name_id = apartment_id)
    # flat_numbers = ApartmentFlat.objects.values_list('flat_number', flat=True)
    blocks = ApartmentBlock.objects.filter(apartment_id=apartment_id)
    apartment = Apartment.objects.get(id=apartment_id)

    # Render the index page with flat numbers
    response = render(request, 'apartment/visitor/visitor_registration.html', {'flat_numbers': flat_numbers, 'apartment': apartment, 'blocks': blocks})
    
    # Set the Cross-Origin-Opener-Policy header for handling popups
    response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    return response

def get_user_info(request):
    user_json_url = request.GET.get('user_json_url')
    
    if not user_json_url:
        return JsonResponse({'error': 'Missing user_json_url parameter'})
    
    try:
        # Fetch user data from phone.email API
        response = requests.get(user_json_url)
        if response.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch user data'})
        
        user_data = response.json()
        
        # Extract phone number from the API response
        phone_number = user_data.get('user_phone_number', '')
        
        # Return success response with phone number
        return JsonResponse({
            'success': True,
            'phone_number': phone_number
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)})

@csrf_exempt
def save_visitor(request):
    if request.method == 'POST':
        try:
            # Get the flat instance
            flat = ApartmentFlat.objects.get(id=request.POST.get('flat'))
            
            # Handle photo upload if present
            photo_url = None
            if 'photo' in request.FILES:
                try:
                    # Generate unique filename
                    file_extension = 'jpg'
                    unique_filename = f"visitor_{uuid.uuid4()}.{file_extension}"
                    
                    # Get the photo file
                    photo_file = request.FILES['photo']
                    
                    # Read the file content
                    file_content = photo_file.read()
                    
                    # Upload to Supabase with retry logic
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            result = supabase.storage.from_(BUCKET_NAME).upload(
                                unique_filename,
                                file_content,
                                {"content-type": "image/jpeg"}
                            )
                            
                            # Get the public URL
                            photo_url = supabase.storage.from_(BUCKET_NAME).get_public_url(unique_filename)
                            print(f"Photo uploaded successfully. URL: {photo_url}")  # Debug log
                            break
                        except Exception as e:
                            if attempt == max_retries - 1:  # Last attempt
                                raise e
                            print(f"Upload attempt {attempt + 1} failed, retrying...")
                            continue
                    
                except Exception as e:
                    print(f"Error uploading photo: {str(e)}")  # Debug log
                    return JsonResponse({
                        'success': False,
                        'error': f'Error uploading photo: {str(e)}'
                    })
            
            # Get location data
            latitude = request.POST.get('latitude')
            longitude = request.POST.get('longitude')
            within_range = request.POST.get('within_range') == 'true'
            
            if not within_range:
                return JsonResponse({
                    'success': False,
                    'error': 'You must be within 50 meters of the apartment to register.'
                })
            
            # Create visitor instance
            visitor = ApartmentVisitor.objects.create(
                name=request.POST.get('name'),
                contact_number=request.POST.get('contact_number'),
                flat=flat,
                block = flat.block_name,
                purpose=request.POST.get('purpose'),
                other_purpose=request.POST.get('other_purpose'),
                photo=photo_url,
                visit_date=timezone.now().date(),
                check_in_time=timezone.now(),
                latitude=latitude,
                longitude=longitude
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Visitor details saved successfully'
            })
            
        except ApartmentFlat.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid flat number'
            })
        except Exception as e:
            print(f"Error saving visitor: {str(e)}")  # Debug log
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        })

def get_flats_by_block(request, block_id):
    """API endpoint to get flats for a specific block."""
    try:
        block = ApartmentBlock.objects.get(id=block_id)
        flats = ApartmentFlat.objects.filter(block_name=block)
        
        # Format flat data for JSON response
        flat_data = [
            {
                'id': flat.id,
                'flat_number': flat.flat_number,
                'block_name': flat.block_name.block_name
            }
            for flat in flats
        ]
        
        return JsonResponse({'flats': flat_data})
    except ApartmentBlock.DoesNotExist:
        return JsonResponse({'error': 'Block not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
