from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from hospitals.models import Hospital

class WebUserManager(BaseUserManager):
    """Custom manager for WebUser model."""
    
    def create_user(self, email, password=None, usertype='patient', **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email)
        user = self.model(email=email, usertype=usertype, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, usertype='super-admin', **extra_fields)


class WebUser(AbstractBaseUser, PermissionsMixin):
    """
    Central user model supporting all 8 HMS roles.
    """
    USER_TYPES = [
        ('super-admin', 'Super Admin'),
        ('hospital-admin', 'Hospital Admin'),
        ('frontdesk', 'Frontdesk / Registration Staff'),
        ('doctor', 'Doctor'),
        ('nurse', 'Nurse'),
        ('pharmacy', 'Pharmacy Staff'),
        ('lab', 'Lab Staff'),
        ('patient', 'Patient'),
    ]

    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255, default='User')
    usertype = models.CharField(max_length=20, choices=USER_TYPES, default='patient')
    hospital = models.ForeignKey(Hospital, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = WebUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'webuser'
        verbose_name = 'Web User'
        verbose_name_plural = 'Web Users'

    def __str__(self):
        return f"{self.email} ({self.get_usertype_display()})"

    # ── Role convenience properties ────────────────────────────────────────
    @property
    def is_super_admin(self):
        return self.usertype == 'super-admin'

    @property
    def is_admin(self):
        return self.usertype in ('super-admin', 'hospital-admin')

    @property
    def is_doctor(self):
        return self.usertype == 'doctor'

    @property
    def is_nurse(self):
        return self.usertype == 'nurse'

    @property
    def is_frontdesk(self):
        return self.usertype == 'frontdesk'

    @property
    def is_pharmacy(self):
        return self.usertype == 'pharmacy'

    @property
    def is_lab(self):
        return self.usertype == 'lab'

    @property
    def is_patient(self):
        return self.usertype == 'patient'

    # Alias for created_at field name used by StaffSerializer
    @property
    def created_at(self):
        return self.date_joined



class SuperAdminOTP(models.Model):
    """
    Temporary OTP storage for Super Admin 2FA authentication flow
    """
    user = models.ForeignKey(WebUser, on_delete=models.CASCADE, related_name='otps')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'super_admin_otps'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp_code}"
