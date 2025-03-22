from functools import wraps
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from .models import *

def hospital_login_required(view_func):
    """Custom decorator to check if a hospital is logged in."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'hospital_id' not in request.session:
            return redirect('hospital_owner_login')  # Redirect to login page
        try:
            hospital = Hospital.objects.get(id=request.session['hospital_id'])
            request.hospital = hospital  # Attach hospital object to request
        except Hospital.DoesNotExist:
            request.session.flush()  # Clear session if hospital does not exist
            return redirect('hospital_owner_login') # Redirect to login page
        return view_func(request, *args, **kwargs)
    return _wrapped_view


from functools import wraps
from django.shortcuts import redirect
from .models import UserHospital

def hospital_user_login_required(view_func):
    """
    Decorator to check if the user is logged in and exists in the UserHospital model.
    Redirects to 'hospital_user_login' if not authenticated or not found.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user_id = request.session.get('user_id')  # Check session for logged-in user ID

        if not user_id:
            return redirect('hospital_user_login')  # Redirect if not logged in

        # Check if the user exists in UserHospital
        if not UserHospital.objects.filter(id=user_id).exists():
            return redirect('hospital_user_login')  # Redirect if not a valid hospital user

        return view_func(request, *args, **kwargs)

    return _wrapped_view

from functools import wraps
from django.shortcuts import redirect
from .models import UserHospital

def require_hospital_permission(required_permission=None):
    """
    Decorator to check if the user is logged in, exists in the UserHospital model, 
    and has the required permission.
    Redirects to 'hospital_user_login' if not authenticated, or 'unauthorized_access' if permission is missing.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = request.session.get('user_id')  # Check session for logged-in user ID

            if not user_id:
                return redirect('hospital_user_login')  # Redirect if not logged in

            # Retrieve user from UserHospital
            try:
                user = UserHospital.objects.get(id=user_id)
            except UserHospital.DoesNotExist:
                return redirect('hospital_user_login')  # Redirect if user does not exist

            # Check if user has the required permission
            if required_permission and required_permission not in user.permissions:
                return redirect('unauthorized_access')  # Redirect if permission is missing

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


#--------------------------------------------------------------------


from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import ObjectDoesNotExist

def hospital_or_user_required(required_permission=None):
    """
    Decorator that allows access if either:
    - The hospital is logged in (hospital_login_required)
    - The user is logged in and has the required permission (require_hospital_permission)
    
    If neither condition is met:
    - Redirects to 'hospital_owner_login' if no hospital is logged in.
    - Redirects to 'hospital_user_login' if no user is logged in.
    - Redirects to 'unauthorized_access' if the user lacks the required permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if a hospital is logged in
            hospital_id = request.session.get('hospital_id')
            if hospital_id:
                try:
                    hospital = Hospital.objects.get(id=hospital_id)
                    request.hospital = hospital  # Attach hospital object to request
                    return view_func(request, *args, **kwargs)  # Access granted
                except Hospital.DoesNotExist:
                    request.session.flush()  # Clear session if hospital does not exist

            # If no hospital is logged in, check for hospital user authentication
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    user = UserHospital.objects.get(id=user_id)
                    if required_permission is None or required_permission in user.permissions:
                        request.user_hospital = user  # Attach user object to request
                        return view_func(request, *args, **kwargs)  # Access granted
                    return redirect('unauthorized_access')  # No permission
                except UserHospital.DoesNotExist:
                    pass  # Continue to redirect below if user doesn't exist

            # If neither a hospital nor an authorized user is found, redirect appropriately
            if not hospital_id and not user_id:
                return redirect('hospital_owner_login')  # Redirect if neither is logged in

            return redirect('hospital_user_login')  # Default redirect for invalid user

        return _wrapped_view
    return decorator


