from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """Compatibility class for existing views needing admin rights (super-admin or hospital-admin)"""
    message = 'Administrator access required.'
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.usertype in ('super-admin', 'hospital-admin')
        )

class IsSuperAdmin(BasePermission):
    message = 'Super Admin access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'super-admin')

class IsHospitalAdmin(BasePermission):
    message = 'Hospital Admin access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'hospital-admin')

class IsFrontDesk(BasePermission):
    message = 'Front Desk access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'frontdesk')

class IsDoctor(BasePermission):
    message = 'Doctor access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'doctor')

class IsNurse(BasePermission):
    message = 'Nurse access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'nurse')

class IsPharmacy(BasePermission):
    message = 'Pharmacy access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'pharmacy')

class IsLab(BasePermission):
    message = 'Laboratory access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'lab')

class IsPatient(BasePermission):
    message = 'Patient access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.usertype == 'patient')

class IsHospitalStaff(BasePermission):
    message = 'Authorized hospital staff access required.'
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.usertype in ('hospital-admin', 'frontdesk', 'doctor', 'nurse', 'pharmacy', 'lab')
        )

# Aliases for backwards compatibility with pre-existing views
IsDoctorUser = IsDoctor
IsPatientUser = IsPatient
IsNurseUser = IsNurse
IsPharmacyUser = IsPharmacy
IsLabUser = IsLab
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.usertype in ('super-admin', 'hospital-admin'):
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'patient') and hasattr(request.user, 'patient_profile'):
            return obj.patient == request.user.patient_profile
        return False
