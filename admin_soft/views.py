from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView, PasswordResetConfirmView
from admin_soft.forms import RegistrationForm, LoginForm, UserPasswordResetForm, UserSetPasswordForm, UserPasswordChangeForm
from django.contrib.auth import logout
# Create your views here.

# Pages
def index(request):
  return render(request, 'pages/index.html', { 'segment': 'dashboard' })

def billing(request):
  return render(request, 'pages/billing.html', { 'segment': 'billing' })

def tables(request):
  return render(request, 'pages/tables.html', { 'segment': 'tables' })

def vr(request):
  return render(request, 'pages/virtual-reality.html', { 'segment': 'virtual_reality' })

def rtl(request):
  return render(request, 'pages/rtl.html', { 'segment': 'rtl' })

def profile(request):
  return render(request, 'pages/profile.html', { 'segment': 'profile' })




# Authentication
class UserLoginView(LoginView):
  template_name = 'accounts/login.html'
  form_class = LoginForm

def register(request):
  if request.method == 'POST':
    form = RegistrationForm(request.POST)
    if form.is_valid():
      form.save()
      print('Account created successfully!')
      return redirect('/accounts/login/')
    else:
      print("Register failed!")
  else:
    form = RegistrationForm()

  context = { 'form': form }
  return render(request, 'accounts/register.html', context)

def logout_view(request):
  logout(request)
  return redirect('/accounts/login/')

class UserPasswordResetView(PasswordResetView):
  template_name = 'accounts/password_reset.html'
  form_class = UserPasswordResetForm

class UserPasswordResetConfirmView(PasswordResetConfirmView):
  template_name = 'accounts/password_reset_confirm.html'
  form_class = UserSetPasswordForm

class UserPasswordChangeView(PasswordChangeView):
  template_name = 'accounts/password_change.html'
  form_class = UserPasswordChangeForm



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta
from .models import *
from .decorators import * #hospital_login_required


def hospital_owner_login(request):
    # Check if the user is already logged in
    if request.session.get('hospital_id'):
        return redirect('hospital_dashboard')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            # Fetch the user from the Hospital model
            hospital = Hospital.objects.get(username=username)

            # Check the password using Django's hashing mechanism
            if check_password(password, hospital.password):
                # Set session data to log the user in
                request.session['hospital_id'] = hospital.id
                request.session['username'] = hospital.username
                messages.success(request, "Login successful.")
                return redirect('hospital_dashboard')  # Redirect to the hospital dashboard

            else:
                messages.error(request, "Invalid credentials. Please try again.")
        except Hospital.DoesNotExist:
            messages.error(request, "Hospital does not exist.")

    return render(request, "hospital_owner_login.html")

def hospital_owner_logout(request):
    request.session.flush()
    messages.success(request, "Successfully logged out.")
    return redirect('hospital_owner_login')

@hospital_login_required
def hospital_dashboard(request):
    hospital_id = request.session.get('hospital_id')
    if not hospital_id:
        messages.error(request, "Please log in to access the dashboard.")
        return redirect('hospital_owner_login')
    try:
        # Fetch hospital details
        hospital = Hospital.objects.get(id=hospital_id)
        doctors = Doctor.objects.filter(hospital=hospital.hospital_name).order_by('name')  # Filter doctors by logged-in user (hospital)
        patients = Patient.objects.filter(hospital=hospital.hospital_name).order_by('name')
        context = {
            'hospital_name': hospital.hospital_name,
            'doctors': doctors,
            'patients': patients,
        }
        return render(request, 'hospital_owner_dashboard.html', context)
    except Hospital.DoesNotExist:
        messages.error(request, "Hospital not found.")
        return redirect('hospital_owner_login')

def add_patient(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        dob = request.POST.get('dob')
        contact = request.POST.get('contact')
        joining_date = request.POST.get('joining_date')  # New joining date field
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name
        Patient.objects.create(name=name, dob=dob, contact=contact, joining_date=joining_date, hospital=hospital_name)
        return redirect('patient_list')  # Redirect to a list or other page after success

    return render(request, 'add_patient.html')

@hospital_or_user_required(required_permission="patient")
def patient_list(request):
    try:
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name
        patients = Patient.objects.filter(hospital=hospital_name).order_by('name')
        return render(request, 'hospital_patient_list.html', {'patients': patients})
    except Hospital.DoesNotExist:
        # user_id = request.session.get('user_id')
        # Username = UserHospital.objects.get(id=user_id)
        # hospital = UserHospital.objects.get(id=user_id, username=Username)
        hospital_name = request.session.get('hospital')
        patients = Patient.objects.filter(hospital=hospital_name)
        return render(request, 'hospital_patient_list.html', {'patients': patients})
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Patient  # Ensure your Patient model is imported
from django.contrib.auth.decorators import login_required


def edit_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)    
    if request.method == 'POST':
        patient.name = request.POST.get('name')
        patient.dob = request.POST.get('dob')
        patient.contact = request.POST.get('contact')
        patient.joining_date = request.POST.get('joining_date')
        patient.save()
        messages.success(request, "Patient details updated successfully!")       
        return redirect('patient_list')  # Replace with your actual URL name
    return render(request, 'hospital_edit_patient.html', {'patient': patient})
 
def delete_patient(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    # if request.method == 'POST':  # To confirm deletion if needed
    patient.delete()
    return redirect('hospital_dashboard')  # Adjust the redirect as needed
    # return redirect('dashboard')  # Default redirect
 
def add_doctor(request):
    """
    Handle the addition of a new doctor to the system.
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        specialty = request.POST.get('specialty')
        contact = request.POST.get('contact')
        joining_date = request.POST.get('joining_date')  # Joining date for the doctor
        username = request.user.username  # Retrieve the username of the logged-in user (hospital name)
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name
        # Create the doctor record
        Doctor.objects.create(name=name, specialty=specialty, contact=contact, joining_date=joining_date, hospital=hospital_name)
        messages.success(request, "Doctor added successfully!")
        return redirect('doctor_list')  # Redirect to the list of doctors after success

    return render(request, 'add_doctor.html')

@require_hospital_permission(required_permission="doctor")
def doctor_list(request):
    """
    Display the list of doctors.
    """
    try:
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        doctors = Doctor.objects.filter(hospital=hospital.hospital_name).order_by('name')  # Filter doctors by logged-in user (hospital)
        return render(request, 'hospitaL_doctor_list.html', {'doctors': doctors})
    except Hospital.DoesNotExist:
        hospital_name = request.session.get('hospital')
        doctors = Doctor.objects.filter(hospital=hospital_name)
        return render(request, 'hospital_doctor_list.html', {'doctors': doctors})
 
def edit_doctor(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    if request.method == 'POST':
        doctor.name = request.POST.get('name')
        doctor.specialty = request.POST.get('specialty')
        doctor.contact = request.POST.get('contact')
        doctor.joining_date = request.POST.get('joining_date')  # Update joining date
        doctor.save()
        messages.success(request, "Doctor details updated successfully!")
        return redirect('doctor_list')

    return render(request, 'hospital_edit_doctor.html', {'doctor': doctor})

 
def delete_doctor(request, doctor_id):
    doctor = Doctor.objects.get(id=doctor_id)
    doctor.delete()
    messages.success(request, "Doctor deleted successfully!")
    return redirect('doctor_list')
 
def manage_medicine(request, pk=None):
    """
    Handle adding or editing a medicine.
    If `pk` is None, a new medicine is created.
    If `pk` is provided, the existing medicine is edited.
    """
    if pk:
        medicine = get_object_or_404(Medicine, pk=pk)
        title = "Edit Medicine"
    else:
        medicine = None
        title = "Add Medicine"
    hospital_id = request.session.get('hospital_id')
    hospital = Hospital.objects.get(id=hospital_id)
    hospital_name = hospital.hospital_name
    if request.method == 'POST':
        name = request.POST.get('name')
        manufacturer = request.POST.get('manufacturer')
        quantity = request.POST.get('quantity')
        price_per_unit = request.POST.get('price_per_unit')
        hospital = hospital_name
        if medicine:  # Editing existing medicine
            medicine.name = name
            medicine.manufacturer = manufacturer
            medicine.quantity = quantity
            medicine.price_per_unit = price_per_unit
            medicine.hospital = hospital
            medicine.save()
            messages.success(request, "Medicine updated successfully!")
        else:  # Creating new medicine
            Medicine.objects.create(
                name=name,
                manufacturer=manufacturer,
                quantity=quantity,
                price_per_unit=price_per_unit,
                hospital=hospital
            )
            messages.success(request, "New medicine added successfully!")

        return redirect('add_medicine')
    medicines = Medicine.objects.filter(hospital=hospital_name).order_by('name')  # Filter doctors by logged-in user (hospital)
    return render(request, 'hospital_medicine_list.html', {'medicines': medicines,'title': title})
 
def delete_medicine(request, pk):
    if request.method == "POST":
        medicine = get_object_or_404(Medicine, pk=pk)
        medicine.delete()
        messages.success(request, f"The medicine '{medicine.name}' was deleted successfully.")
        return redirect('add_medicine')  # Replace 'medicine_list' with your list view URL name
    return redirect('add_medicine')  # Replace with your list view URL name

def hospital_user_login(request):
    if request.session.get('user_id'):
        return redirect('hospital_user_dashboard')  # Redirect if already logged in
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            # Fetch the user from the UserHospital model
            user_details = UserHospital.objects.get(username=username)

            # Check the password using Django's hashing mechanism
            if check_password(password, user_details.password):
                # Set session data to log the user in
                request.session['user_id'] = user_details.id
                request.session['username'] = user_details.username
                messages.success(request, "Login successful.")
                return redirect("hospital_user_dashboard")  # Redirect to the hospital dashboard
            else:
                messages.error(request, "Invalid credentials. Please try again.")
        except UserHospital.DoesNotExist:
            messages.error(request, "User does not exist.")

    return render(request, "hospital_user_login.html")

import json
from django.shortcuts import render, redirect
from .models import UserHospital
@hospital_user_login_required
def hospital_user_dashboard_view(request):
    if not request.session.get('user_id'):
        return redirect("hospital_user_login")  # Redirect to login if not authenticated
    
    user_id = request.session.get('user_id')
    username = request.session.get('username')

    try:
        user = UserHospital.objects.get(id=user_id)
        
        # Check if permissions is stored as a list or JSON string
        if isinstance(user.permissions, str):  
            permissions = json.loads(user.permissions)  # Convert JSON string to list
        else:
            permissions = user.permissions  # Already a list
        
    except UserHospital.DoesNotExist:
        return redirect("hospital_user_login")  # Redirect if user not found

    return render(request, "hospital_user_dashboard.html", {
        "username": username,
        "user_id": user_id,
        "permissions": permissions
    })


def hospital_user_logout(request):
    request.session.flush()  # Clear the session
    messages.success(request, "You have been logged out.")
    return redirect("hospital_user_login")

def hospital_user_profile_view(request, user_id):
    """
    View function to display the profile of a hospital user.
    """
    user = get_object_or_404(UserHospital, id=user_id)
    return render(request, 'hospital_user_profile.html', {'user': user})

#-----------------------------------------------------------------
def view_available_slots(request):
    hospital_id = request.session.get('hospital_id')
    hospital = Hospital.objects.get(id=hospital_id)
    hospital_name = hospital.hospital_name
    slots = AvailableSlot.objects.filter(hospital=hospital_name, is_booked=False)
    return render(request, 'hospital_view_available_slots.html', {'slots': slots})

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Doctor, AvailableSlot, Patient, Appointment

def check_available_slots(request):
    """
    Handles AJAX request to fetch available slots for a given doctor and date.
    """
    doctor_id = request.GET.get('doctor_id')
    date = request.GET.get('date')

    if doctor_id and date:
        available_slots = AvailableSlot.objects.filter(
            doctor_id=doctor_id, date=date, is_booked=False
        ).values('id', 'start_time', 'end_time')

        return JsonResponse({'available_slots': list(available_slots)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Doctor, AvailableSlot, Patient, Appointment

def book_appointment(request):
    """
    Handles appointment booking.
    """
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        patient_id = request.POST.get('patient')
        date = request.POST.get('date')
        slot_id = request.POST.get('slot')
        reason = request.POST.get('reason')
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name
        if not (doctor_id and patient_id and date and slot_id and reason):
            return render(request, 'hospital_book_appointment.html', {
                'error': 'All fields are required!',
                'doctors': Doctor.objects.filter(hospital=hospital_name),
                'patients': Patient.objects.filter(hospital=hospital_name),
                'available_slots': AvailableSlot.objects.filter(is_booked=False, hospital=hospital_name)
            })

        # Get the slot object
        slot = AvailableSlot.objects.get(id=slot_id)

        # Ensure the slot is not already booked
        if slot.is_booked:
            return render(request, 'hospital_book_appointment.html', {
                'error': 'This slot is already booked. Please choose another.',
                'doctors': Doctor.objects.filter(hospital=hospital_name),
                'patients': Patient.objects.filter(hospital=hospital_name),
                'available_slots': AvailableSlot.objects.filter(is_booked=False, hospital=hospital_name)
            })

        # Create an appointment (no need to manually add start_time and end_time)
        appointment = Appointment.objects.create(
            doctor=slot.doctor,
            patient_id=patient_id,
            date=date,
            slot=slot,
            reason=reason,
            hospital=hospital_name  # Assuming hospital is stored in AvailableSlot
        )

        # Mark slot as booked
        slot.is_booked = True
        slot.save()

        return redirect('hospital_appointment_list')

    else:
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name
        doctors = Doctor.objects.filter(hospital=hospital_name)
        patients = Patient.objects.filter(hospital=hospital_name)
        return render(request, 'hospital_book_appointment.html', {
            'doctors': doctors,
            'patients': patients
        })

def appointment_list(request):
    """View for listing all appointments"""
    hospital_id = request.session.get('hospital_id')
    hospital = Hospital.objects.get(id=hospital_id)
    hospital_name = hospital.hospital_name
    appointments = Appointment.objects.filter(hospital=hospital_name)
    return render(request, 'hospital_appointment_list.html', {'appointments': appointments})

@csrf_exempt  # Use if you're not using AJAX with CSRF token headers
def update_appointment_status(request, appointment_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')

            if new_status not in ['Scheduled', 'Completed', 'Canceled']:
                return JsonResponse({'success': False, 'message': 'Invalid status'})

            # Get the appointment
            appointment = Appointment.objects.get(id=appointment_id)

            # Check if the appointment's current status is "Scheduled"
            if appointment.status != 'Scheduled':
                return JsonResponse({'success': False, 'message': 'Cannot update status'})

            # Update the status of the appointment
            appointment.status = new_status
            appointment.save()

            # If the status is canceled, mark the slot as available
            if new_status == 'Canceled':
                # Get the slot associated with the appointment
                slot = appointment.slot
                # Set the slot's is_booked to False
                slot.is_booked = False
                slot.save()

            return JsonResponse({'success': True, 'message': 'Status updated successfully'})

        except Appointment.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Appointment not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})
#--------------------------------------------------------------------------------

def add_available_slot(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        date = request.POST.get('date')
        start_times = request.POST.getlist('start_time[]')  # Get all start times
        end_times = request.POST.getlist('end_time[]')      # Get all end times
        interval = int(request.POST.get('interval'))
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name

        # Get the doctor object
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            messages.error(request, "Doctor not found.")
            return redirect('add_available_slot')

        # Loop through each time range
        for start_time_str, end_time_str in zip(start_times, end_times):
            # Convert time strings to datetime objects
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # Generate available slots based on interval
            current_time = datetime.combine(datetime.today(), start_time)
            end_datetime = datetime.combine(datetime.today(), end_time)

            while current_time.time() < end_time:
                slot_end_time = (current_time + timedelta(minutes=interval)).time()
                if slot_end_time > end_time:
                    break  # Stop if the next slot exceeds the end time

                # Check if the slot already exists
                existing_slot = AvailableSlot.objects.filter(
                    doctor=doctor,
                    date=date,
                    start_time=current_time.time(),
                    end_time=slot_end_time
                ).exists()

                if existing_slot:
                    messages.warning(request, f"Slot {current_time.time()} - {slot_end_time} already exists!")
                else:
                    # Create a new available slot
                    available_slot = AvailableSlot(
                        doctor=doctor,
                        date=date,
                        start_time=current_time.time(),
                        end_time=slot_end_time,
                        interval=interval,
                        hospital=hospital_name,
                        is_booked=False
                    )
                    available_slot.save()

                # Move to the next slot
                current_time += timedelta(minutes=interval)

        messages.success(request, "Available slots have been added successfully!")
        return redirect('view_available_slots')

    else:
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital_name = hospital.hospital_name
        doctors = Doctor.objects.filter(hospital=hospital_name)
        return render(request, 'hospital_add_available_slot.html', {'doctors': doctors})
 
def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        contact_number = request.POST.get('contact')
        email = request.POST.get('email')
        role = request.POST.get('userRole')
        permissions = request.POST.getlist('permissions[]')  # Checklist
        hospital_id = request.session.get('hospital_id')
        hospital = Hospital.objects.get(id=hospital_id)
        hospital = hospital.hospital_name

        # Validation
        if UserHospital.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('create_user')
        if UserHospital.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('create_user')

        # Create the new user
        new_user = UserHospital(
            username=username,
            password=make_password(password),  # Hash password
            contact_number=contact_number,
            email=email,
            role=role,
            permissions=permissions,
            hospital=hospital,
        )
        new_user.save()  # `hospital` is assigned automatically in the model's `save()`

        messages.success(request, "User created successfully!")
        return redirect('create_user')

    return render(request, 'hospital_create_user.html')  # Render the form



def user_hospital_list(request):
    hospital_id = request.session.get('hospital_id')
    hospital = Hospital.objects.get(id=hospital_id)
    hospital_name = hospital.hospital_name
    users = UserHospital.objects.filter(hospital=hospital_name).order_by('username')
    return render(request, 'user_hospital_list.html', {'users': users})

#@require_hospital_permission(required_permission="doctor")
# @hospital_or_user_required(required_permission="patient")
def hospital_sample(request):
    return render(request, 'sample.html')