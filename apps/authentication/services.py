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
        Dispatch the OTP code to Super Admin via email SMTP with a premium HTML template.
        """
        subject = 'eDoc HMS - Super Admin 2FA Code'
        
        # Plain text fallback
        plain_message = f"Hello,\n\nYour 2FA verification code for eDoc HMS Super Admin portal is: {otp.otp_code}\n\nThis code will expire in 5 minutes.\n\nRegards,\neDoc HMS Team"
        
        # Premium responsive HTML template
        html_message = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>eDoc HMS - Super Admin 2FA Code</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed; background-color: #f4f6f9; padding: 40px 0;">
    <tbody>
      <tr>
        <td align="center" valign="top">
          <!-- Outer Container Card -->
          <table border="0" cellpadding="0" cellspacing="0" width="500" style="max-width: 500px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(15, 26, 46, 0.05); overflow: hidden; border: 1px solid #eef2f6;">
            <tbody>
              <!-- Header -->
              <tr>
                <td style="background-color: #0f1a2e; padding: 25px; text-align: center;">
                  <div style="display: inline-block; vertical-align: middle; color: #ffffff; font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">
                    eDoc <span style="color: #0ea5e9;">HMS</span>
                  </div>
                </td>
              </tr>
              
              <!-- Content Body -->
              <tr>
                <td style="padding: 40px 30px; color: #334155; font-size: 16px; line-height: 1.6;">
                  <h3 style="margin-top: 0; color: #0f1a2e; font-size: 20px; font-weight: 700; margin-bottom: 20px; text-align: center;">Two-Factor Authentication</h3>
                  <p style="margin: 0 0 20px 0; color: #475569;">Hello Super Admin,</p>
                  <p style="margin: 0 0 24px 0; color: #475569;">We received a login request for the eDoc HMS Super Admin portal. Please use the following 6-digit verification code to complete your authentication process:</p>
                  
                  <!-- OTP Display Card -->
                  <div style="background-color: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 24px;">
                    <div style="font-size: 36px; font-weight: 800; letter-spacing: 6px; color: #0ea5e9; font-family: 'Courier New', Courier, monospace;">{otp.otp_code}</div>
                  </div>
                  
                  <!-- Expiry warning -->
                  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #fef2f2; border-left: 4px solid #ef4444; border-radius: 4px; margin-bottom: 24px;">
                    <tbody>
                      <tr>
                        <td style="padding: 12px 16px; color: #991b1b; font-size: 14px; font-weight: 500; line-height: 1.4;">
                          This verification code is strictly confidential and will expire in <strong>5 minutes</strong>. If you did not request this code, please secure your account credentials immediately.
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  
                  <p style="margin: 0 0 4px 0; color: #64748b; font-size: 14px;">Regards,</p>
                  <p style="margin: 0; color: #0f1a2e; font-weight: 600; font-size: 15px;">eDoc Operations Command</p>
                </td>
              </tr>
              
              <!-- Footer -->
              <tr>
                <td style="background-color: #f8fafc; border-top: 1px solid #f1f5f9; padding: 20px 30px; text-align: center; color: #94a3b8; font-size: 12px;">
                  This is an automated security transmission from eDoc HMS. Please do not reply directly to this email.
                </td>
              </tr>
            </tbody>
          </table>
        </td>
      </tr>
    </tbody>
  </table>
</body>
</html>
"""

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [otp.user.email],
                fail_silently=False,
                html_message=html_message
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
