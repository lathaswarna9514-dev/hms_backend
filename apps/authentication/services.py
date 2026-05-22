import logging
import random
import string
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import WebUser, SuperAdminOTP

logger = logging.getLogger('edoc_hms')

class AuthService:
    """Handles authentication business logic and OTP management."""

    @staticmethod
    def generate_otp(user):
        """
        Generate a secure 6-digit OTP code, invalidate previous active OTPs for the user,
        and set a 5-minute expiry countdown.
        """
        # Invalidate existing unexpired OTPs
        SuperAdminOTP.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate 6 digit code
        code = ''.join(random.choices(string.digits, k=6))
        expiry = timezone.now() + timezone.timedelta(minutes=settings.OTP_EXPIRY_MINUTES)

        otp = SuperAdminOTP.objects.create(
            user=user,
            otp_code=code,
            expires_at=expiry
        )
        return otp

    @staticmethod
    def send_otp_email(otp):
        """
        Dispatch the OTP code to Super Admin via email SMTP.
        """
        subject = 'eDoc HMS - Super Admin 2FA Code'
        message = f"Hello,\n\nYour 2FA verification code for eDoc HMS Super Admin portal is: {otp.otp_code}\n\nThis code will expire in 5 minutes.\n\nRegards,\neDoc HMS Team"
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [otp.user.email],
                fail_silently=False,
            )
            logger.info(f"OTP email sent successfully to {otp.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            return False

    @staticmethod
    def verify_otp(user, code):
        """
        Validate OTP code. Returns tuple (success, message).
        """
        try:
            otp = SuperAdminOTP.objects.filter(
                user=user,
                otp_code=code,
                is_used=False
            ).latest('created_at')
        except SuperAdminOTP.DoesNotExist:
            return False, "Invalid verification code."

        if otp.is_expired():
            otp.is_used = True
            otp.save()
            return False, "Verification code has expired."

        # Success - mark used and verified
        otp.is_used = True
        otp.is_verified = True
        otp.save()
        return True, "Verified successfully."
