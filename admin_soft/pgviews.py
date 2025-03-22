from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib.auth.views import *
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from admin_soft.forms import *
from .models import *
from django.utils import timezone
from datetime import date

class PGLoginViewOwner(View):
    template_name = 'pg/pg_owner_login.html'
    form_class = PGLoginFormOwner

    def get(self, request, *args, **kwargs):
        """If already logged in, redirect to dashboard"""
        if request.session.get("pg_id"):  # Check if PG owner is logged in
            return redirect("pg_owner_dashboard")
        
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """Handle login authentication"""
        if request.session.get("pg_id"):  # If already logged in, redirect to dashboard
            return redirect("pg_owner_dashboard")

        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            try:
                pg = PG.objects.get(name=username)  # Assuming `name` is the username field
                
                if check_password(password, pg.password):  # Check hashed password
                    request.session["pg_id"] = pg.id  # Store PG owner details in session
                    request.session["pg_name"] = pg.pg_name
                    messages.success(request, "Login successful.")
                    return redirect("pg_owner_dashboard")
                else:
                    messages.error(request, "Invalid password.")
            except PG.DoesNotExist:
                messages.error(request, "PG Owner does not exist.")

        return render(request, self.template_name, {"form": form})



def pg_owner_logout(request):
    """Logout PG Owner and clear session"""
    logout(request)  # Logs out the user
    request.session.flush()  # Clears all session data
    messages.success(request, "You have been logged out successfully.")
    return redirect("pg_owner_login")  # Redirect to the login page


# @login_required
def pg_owner_dashboard(request):
    """PG Owner Dashboard View"""
    pg_id = request.session.get("pg_id")
    pg_name = request.session.get("pg_name")

    if not pg_id:
        messages.error(request, "You must be logged in to access this page.")
        return redirect("pg_owner_login")  # Redirect to login if session is missing

    context = {
        "pg_name": pg_name,
    }
    return render(request, "pg/pg_owner_dashboard.html", context)

def room_dashboard(request):
    pg_id = request.session.get("pg_id")  # Retrieve PG ID from session

    if not pg_id:
        messages.error(request, "You must be logged in to access this page.")
        return redirect("pg_owner_login")  # Redirect to login if not authenticated

    try:
        pg = PG.objects.get(id=pg_id)  # Fetch PG instance
        update_bed_status(pg.pg_name)
        rooms = Room.objects.filter(pg_name=pg.pg_name).order_by('room_number')
        
        room_data = []
        for room in rooms:
            beds = Bed.objects.filter(pg_name=pg.pg_name, room_id=room.id)
            vacant_beds = beds.filter( is_vacant=False).count()
            if vacant_beds == 0:
                if room.status!='maintenance':
                    room.status = 'occupied'
                    room.save()
            else:
                if room.status!='maintenance':
                    room.status = 'available'
                    room.save()
            occupied_beds = beds.filter(is_vacant=True).count()
            room_data.append({
                "room": room,
                "vacant_beds": vacant_beds,
                "occupied_beds": occupied_beds,
            })
        context = {
            'rooms': rooms,
            'room_datas': room_data,
            'pg_name': pg.pg_name,
            'total_rooms': rooms.count(),
            'available_rooms': rooms.filter(status='available').count(),
            'occupied_rooms': rooms.filter(status='occupied').count(),
            'maintenance_rooms': rooms.filter(status='maintenance').count(),
        }
        return render(request, 'pg/owner_room_dashboard.html', context)
    except PG.DoesNotExist:
        messages.error(request, "PG not found. Please log in again.")
        return redirect("pg_owner_login")


def add_room(request):
    """View to add a new room under the logged-in PG owner"""
    pg_id = request.session.get("pg_id")  # Retrieve PG ID from session

    if not pg_id:
        messages.error(request, "You must be logged in to add a room.")
        return redirect("pg_owner_login")  # Redirect to login if not authenticated

    try:
        pg = PG.objects.get(id=pg_id)  # Fetch PG instance
    except PG.DoesNotExist:
        messages.error(request, "PG not found. Please log in again.")
        return redirect("pg_owner_login")
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)  # Don't save yet
            room.pg_name = pg.pg_name  # Assign the PG owner
            room.save()  # Save the room with PG association
            for bed_number in range(1, room.number_of_beds + 1):
                Bed.objects.create(room=room, bed_number=bed_number, is_vacant=False, pg_name=pg.pg_name)
            messages.success(request, "Room and beds added successfully!")
            return redirect('room_dashboard')
    else:
        form = RoomForm()
    return render(request, 'pg/room_form.html', {'form': form})


def update_bed_status(pg_name):
    """ Update bed status: Set is_vacant to False only if not used by a tenant and not under maintenance. """
    beds = Bed.objects.filter(pg_name=pg_name)
    for bed in beds:
        # Skip beds in maintenance rooms
        if bed.room.status == "maintenance":
            continue  

        # Check if the bed is assigned to a tenant
        is_assigned = Tenant.objects.filter(assigned_bed=bed).exists()

        if not is_assigned:
            bed.is_vacant = False  # Set as vacant
        else:
            bed.is_vacant = True  # Mark as occupied
        bed.save()



def edit_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    if request.method == "POST":
        room.room_number = request.POST.get("room_number")
        room.number_of_beds = request.POST.get("number_of_beds")
        room.rent_amount = request.POST.get("rent_amount")
        room.status = request.POST.get("status")
        print(room.status)
        room.save()
        messages.success(request, "Room details updated successfully!")
        return redirect("room_dashboard")  # Change this to your actual dashboard URL name

    return render(request, "pg/owner_room_edit.html", {"room": room})


def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        room.delete()
        return redirect('room_dashboard')
    room.delete()
    return redirect('room_dashboard')


def pg_owner_tenant_dashboard(request):
    pg_id = request.session.get("pg_id")  # Retrieve PG ID from session
    if not pg_id:
        messages.error(request, "You must be logged in to add a tenant.")
        return redirect("pg_owner_login") 
    try:
        print("try")
        pg = PG.objects.get(id=pg_id)
        update_bed_status(pg.pg_name)
        room = Room.objects.filter(pg_name=pg.pg_name)
        bed = Bed.objects.filter(pg_name=pg.pg_name)
    except PG.DoesNotExist:
        messages.error(request, "PG not found. Please log in again.")

    if request.method == 'POST':
        form = TenantForm(request.POST, request.FILES)
        if form.is_valid():
            tenant = form.save(commit=False)  # Don't save yet
            assigned_bed = form.cleaned_data.get("assigned_bed")
            print(assigned_bed)
            room_number, bed_number = "Unknown", "Unknown"
            match = re.search(r"Room (\d+) - Bed (\d+)", str(assigned_bed))
            if match:
                room_number = int(match.group(1))
                print(room_number)
                bed_number = f"Bed {match.group(2)}"
            room_amount = Room.objects.get(room_number=room_number)
            tenant.payment_amount = room_amount.rent_amount
            tenant.pg_name = pg.pg_name  # Assign the PG owner
            tenant.save()

            # Mark the assigned bed as occupied
            assigned_bed = form.cleaned_data.get("assigned_bed")  # Get bed from cleaned data
            if assigned_bed:
                assigned_bed.is_vacant = True  # Mark bed as occupied
                assigned_bed.save()

            return redirect('pg_owner_tenant_dashboard')
    else:
        form = TenantForm(request=request)
    pg_name = pg.pg_name
    tenants = Tenant.objects.filter(pg_name=pg_name)
    context = {
        'form': form,
        'tenants': tenants,
        'rooms': room, 
        'beds': bed,
        'pg_name': pg_name,
    }
    return render(request, 'pg/owner_tenant_dashboard.html', context)


def edit_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    old_bed=tenant.assigned_bed
    if request.method == "POST":
        form = TenantForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            # Update assigned bed status
            assigned_bed = form.cleaned_data.get("assigned_bed")
            if assigned_bed and assigned_bed != old_bed:
                assigned_bed = form.cleaned_data.get("assigned_bed")
                room_number, bed_number = "Unknown", "Unknown"
                match = re.search(r"Room (\d+) - Bed (\d+)", str(assigned_bed))
                if match:
                    room_number = match.group(1)
                    bed_number = f"Bed {match.group(2)}"
                room_amount = Room.objects.get(room_number=room_number)
                tenant.payment_amount = room_amount.rent_amount
                # Free the previous bed if changed
                if tenant.assigned_bed:
                    tenant.assigned_bed.is_vacant = True
                    tenant.assigned_bed.save()

                    old_bed.is_vacant = False
                    old_bed.save()

            tenant.save()
            messages.success(request, "Tenant details updated successfully!")
            return redirect('pg_owner_tenant_dashboard')  # Redirect to the tenant list

    else:
        form = TenantForm(instance=tenant)

    return render(request, 'pg/owner_tenant_edit.html', {'form': form, 'tenant': tenant})

def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    
    if request.method == "POST":
        tenant.delete()
        messages.success(request, "Tenant deleted successfully.")
    
    return redirect('pg_owner_tenant_dashboard')  # Redirect to the tenant list page


def pg_owner_profile(request):
    # Fetch the first PG owner profile (assuming there's only one owner)
    try:
        pg_id = request.session.get("pg_id")
        pgowner = get_object_or_404(PG, id=pg_id)  # Change ID logic as needed
        return render(request, 'pg/pg_owner_profile.html', {'pgowner': pgowner})
    except:
        return redirect('pg_owner_login')
 
def pg_owner_profile_edit(request):
    pg_id = request.session.get("pg_id")
    pgowner = get_object_or_404(PG, id=pg_id)  # Fetch PG Owner Profile

    if request.method == "POST":
        form = PgOwnerProfileForm(request.POST, instance=pgowner)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('pg_owner_profile')  # Redirect to profile page after update
    else:
        form = PgOwnerProfileForm(instance=pgowner)

    return render(request, 'pg/pg_owner_profile_edit.html', {'form': form, 'pgowner': pgowner})

def owner_complaints(request):
    pg_id = request.session.get("pg_id")
    pgowner = get_object_or_404(PG, id=pg_id)
    owner_pg_name = pgowner.pg_name  # Assuming the logged-in owner has a `pg_name`
    
    complaints = Complaint.objects.filter(tenant__pg_name=owner_pg_name)  # Filter complaints by PG name

    return render(request, "pg/owner_complaints.html", {
        'complaints': complaints
    })

def owner_payments(request):
    pg_id = request.session.get("pg_id")
    pgowner = get_object_or_404(PG, id=pg_id)
    owner_pg_name = pgowner.pg_name
    payments = Payment.objects.filter(tenant__pg_name=owner_pg_name)

    return render(request, "pg/owner_payments.html", {
        'payments': payments
    })


def manage_pg(request):
    context = {
        "segment": "manage_pg",
        "pg_list": [
            {"name": "Sunrise PG", "location": "Downtown", "owner": "Mr. Raj"},
            {"name": "Green Valley PG", "location": "Uptown", "owner": "Ms. Priya"},
        ],
    }
    return render(request, "pg/manage_pg.html", context)



#----------------------------------------------------------------

class TenantLoginView(View):
    template_name = 'tenant/pg_tenant_login.html'
    form_class = PGLoginFormTenant

    def get(self, request, *args, **kwargs):
        """If already logged in, redirect to tenant dashboard"""
        if request.session.get("tenant_id"):  # Check if Tenant is logged in
            return redirect("pg_tenant_dashboard")

        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        """Handle tenant login authentication"""
        if request.session.get("tenant_id"):  # If already logged in, redirect to dashboard
            return redirect("pg_tenant_dashboard")

        form = self.form_class(request.POST)
        if form.is_valid():
            email = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            try:
                tenant = Tenant.objects.get(name=email)  # Assuming `email` is the login field
                print('hai')
                if check_password(password, tenant.password):
                    print('if hai')  # Check hashed password
                    request.session["tenant_id"] = tenant.id  # Store Tenant details in session
                    request.session["tenant_name"] = tenant.name
                    messages.success(request, "Login successful.")
                    return redirect("pg_tenant_dashboard")
                else:
                    messages.error(request, "Invalid password.")
            except Tenant.DoesNotExist:
                messages.error(request, "Tenant does not exist.")

        return render(request, self.template_name, {"form": form})



import re

def tenant_dashboard(request):
    """Display the tenant dashboard with relevant details."""
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_tenant_login")
    tenant_payment_view(request, tenant_id)
    tenant = Tenant.objects.get(id=tenant_id)
    payments = Payment.objects.filter(tenant=tenant).order_by("-payment_date")
    complaints = Complaint.objects.filter(tenant=tenant).order_by("-created_at")
    # Extract Room and Bed details
    room_number, bed_number = "Unknown", "Unknown"
    match = re.search(r"Room (\d+) - Bed (\d+)", str(tenant.assigned_bed))
    if match:
        room_number = f"Room {match.group(1)}"
        bed_number = f"Bed {match.group(2)}"


    payment_status = "Pending" if tenant.due_amount > 0 else "Paid"

    context = {
        "tenant": tenant,
        "payments": payments,
        "complaints": complaints,
        "payment_status": payment_status,
        "room_number": room_number,
        "bed_number": bed_number,
    }
    return render(request, "tenant/pg_tenant_dashboard.html", context)


def pg_tenant_profile(request):
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_tenant_login")
    tenant = Tenant.objects.get(id=tenant_id) # Assuming tenant is related to user
    return render(request, "tenant/pg_tenant_profile.html", {'tenant': tenant})

def pg_tenant_edit_profile(request):
    tenant_id = request.session.get("tenant_id")
    
    if not tenant_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_tenant_login")
    tenant = Tenant.objects.get(id=tenant_id)  # Assuming tenant is related to user
    pg_name=tenant.pg_name
    if request.method == "POST":
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            form.save()  # Save changes to the tenant object
            update_bed_status(pg_name)
            return redirect('pg_tenant_profile')  # Redirect to the profile page
    else:
        form = TenantForm(instance=tenant)  # Prepopulate the form with the current tenant data

    return render(request, "tenant/pg_tenant_profile_edit.html", {'form': form})

def pg_tenant_payments(request):
    tenant_id = request.session.get("tenant_id")
    tenant_payment_view(request, tenant_id)
    if not tenant_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_tenant_login")
    tenant = Tenant.objects.get(id=tenant_id)  # Assuming tenant is related to the user    
    payment_history = Payment.objects.filter(tenant=tenant).order_by('-payment_date')
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.tenant = tenant  # Associate the payment with the tenant
            payment.status = 'Pending'  # Set initial status as 'Pending'
            payment.save()
            return redirect('pg_tenant_payments')  # Redirect to the payment history page
    else:
        form = PaymentForm()
    # pg_tenant_make_payment(request, tenant)
        return render(request, "tenant/pg_tenant_payments.html", {
            'tenant': tenant,
            'payment_history': payment_history,
            'form': form
        })


def pg_tenant_complaints(request):
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_tenant_login")
    tenant = Tenant.objects.get(id=tenant_id)
    
    complaints = Complaint.objects.filter(tenant=tenant)  # Get all complaints for the logged-in tenant

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.tenant = tenant  # Assign the logged-in tenant
            complaint.save()
            messages.success(request, "Your complaint has been submitted successfully.")
            return redirect('pg_tenant_complaints')  # Redirect to avoid resubmission on page refresh
    else:
        form = ComplaintForm()

    return render(request, "tenant/pg_tenant_complaints.html", {
        'complaints': complaints,
        'form': form
    })

def pg_tenant_logout(request):
    # Logs the user out
    logout(request)
    
    # Redirects to the login page or homepage after logout
    return redirect('pg_tenant_login')

def pg_tenant_make_payment(request, tenant):
    tenant_id = request.session.get("tenant_id")
    if not tenant_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_tenant_login")
    tenant = Tenant.objects.get(id=tenant_id) 
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.tenant = tenant  # Associate the payment with the tenant
            payment.status = 'Pending'  # Set initial status as 'Pending'
            payment.save()
            return redirect('pg_tenant_payments')  # Redirect to the payment history page
    else:
        form = PaymentForm()
    return render(request, "tenant/pg_tenant_make_payment.html", {'form': form})

def resolve_complaint(request, complaint_id):
    pg_id = request.session.get("pg_id")
    
    if not pg_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_owner_login")

    complaint = get_object_or_404(Complaint, id=complaint_id)

    if complaint.status != 'Resolved':
        complaint.status = 'Resolved'
        complaint.resolved_at = timezone.now()  # Set the resolved time
        complaint.save()
        messages.success(request, f"Complaint by {complaint.tenant.name} has been resolved.")
    else:
        messages.warning(request, "This complaint is already marked as resolved.")

    return redirect('owner_complaints')  # Redirect to the complaints page

def mark_payment_completed(request, payment_id):
    pg_id = request.session.get("pg_id")
    
    if not pg_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_owner_login")

    payment = get_object_or_404(Payment, id=payment_id)

    if payment.status != 'Completed':
        payment.status = 'Completed'
        payment.save()
        messages.success(request, f"Payment of ₹{payment.amount} has been marked as completed.")
    else:
        messages.warning(request, "This payment is already marked as completed.")

    return redirect('owner_payments')  # Redirect to the payments page

def mark_payment_failed(request, payment_id):
    pg_id = request.session.get("pg_id")
    
    if not pg_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect("pg_owner_login")

    payment = get_object_or_404(Payment, id=payment_id)

    if payment.status != 'Failed':
        payment.status = 'Failed'
        payment.save()
        messages.success(request, f"Payment of ₹{payment.amount} has been marked as Failed.")
    else:
        messages.warning(request, "This payment is already marked as completed.")

    return redirect('owner_payments')

def tenant_payment_view(request, tenant_id):
    tenant = get_object_or_404(Tenant, id=tenant_id)
    if tenant.check_in_date:
        today = date.today()
        months_elapsed = (today.year - tenant.check_in_date.year) * 12 + (today.month - tenant.check_in_date.month)
        if today.day >= tenant.check_in_date.day:
            months_elapsed += 1
    else:
        months_elapsed = 0
    total_expected = months_elapsed * tenant.payment_amount
    payment_history = Payment.objects.filter(tenant=tenant)   
    total_amount_paid =  sum(payment.amount for payment in payment_history if payment.status == 'Completed')
    
    if total_amount_paid >= total_expected:
        advance_amount = total_amount_paid - total_expected
        due_amount = 0
    else:
        advance_amount = 0
        due_amount = total_expected - total_amount_paid
    tenant.due_amount = due_amount
    tenant.advance_amount = advance_amount
    tenant.total_amount_paid = total_amount_paid
    tenant.save(update_fields=['due_amount', 'advance_amount', 'total_amount_paid'])


#------------------------

from django.shortcuts import render
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from .models import Payment, Room

def dashboard_view(request):
    # Aggregate monthly payment data for completed payments
    payment_data = (
        Payment.objects.filter(status='Completed')
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(total_amount=Sum('amount'), count=Count('id'))
        .order_by('month')
    )

    # Prepare data lists for the payment chart
    labels = [entry['month'].strftime("%B %Y") for entry in payment_data]
    totals = [float(entry['total_amount']) for entry in payment_data]
    counts = [entry['count'] for entry in payment_data]

    # Aggregate room status distribution data
    room_status_data = Room.objects.values('status').annotate(count=Count('id'))
    room_labels = [entry['status'].capitalize() for entry in room_status_data]
    room_counts = [entry['count'] for entry in room_status_data]

    context = {
        'labels': labels,
        'totals': totals,
        'counts': counts,
        'room_labels': room_labels,
        'room_counts': room_counts,
    }
    return render(request, 'pg/pg_owner_dashboard.html', context)
