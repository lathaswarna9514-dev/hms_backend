from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import WebUser, SuperAdminOTP
from django.utils import timezone

class TokenAuthAndRotationTests(APITestCase):
    def setUp(self):
        # Create a standard patient user
        self.patient_password = 'TestPassword123!'
        self.patient = WebUser.objects.create_user(
            email='patient@example.com',
            password=self.patient_password,
            usertype='patient',
            name='John Patient'
        )

        # Create a super-admin user
        self.sa_password = 'SaPassword123!'
        self.sa = WebUser.objects.create_user(
            email='sa@example.com',
            password=self.sa_password,
            usertype='super-admin',
            name='Super Admin'
        )

    def test_patient_login_and_token_retrieval(self):
        """
        Verify that a regular user (patient) can log in and retrieve both
        access and refresh tokens immediately.
        """
        login_url = reverse('login')
        data = {
            'email': self.patient.email,
            'password': self.patient_password
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        res_data = response.data
        self.assertTrue(res_data['success'])
        self.assertFalse(res_data['require_2fa'])
        self.assertIn('access', res_data['data'])
        self.assertIn('refresh', res_data['data'])
        self.assertEqual(res_data['data']['user']['email'], self.patient.email)

    def test_token_rotation_and_blacklisting(self):
        """
        Verify that refreshing a token rotates it (returns new access and refresh tokens)
        and blacklists the old refresh token.
        """
        # 1. Login to get tokens
        login_url = reverse('login')
        data = {
            'email': self.patient.email,
            'password': self.patient_password
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        initial_refresh_token = response.data['data']['refresh']
        initial_access_token = response.data['data']['access']

        # 2. Call token refresh endpoint
        refresh_url = reverse('token-refresh')
        refresh_data = {'refresh': initial_refresh_token}
        
        # Perform the first refresh
        refresh_response = self.client.post(refresh_url, refresh_data)
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        new_access_token = refresh_response.data.get('access')
        new_refresh_token = refresh_response.data.get('refresh')
        
        self.assertIsNotNone(new_access_token)
        self.assertIsNotNone(new_refresh_token)
        
        # Verify rotation (new tokens are different)
        self.assertNotEqual(initial_access_token, new_access_token)
        self.assertNotEqual(initial_refresh_token, new_refresh_token)

        # 3. Attempt to refresh again using the OLD refresh token.
        # It should fail because the old refresh token was blacklisted.
        failed_refresh_response = self.client.post(refresh_url, refresh_data)
        self.assertEqual(failed_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(failed_refresh_response.data['success'])
        self.assertEqual(failed_refresh_response.data['message'], 'Token is blacklisted')

    def test_super_admin_2fa_and_token_retrieval(self):
        """
        Verify the super-admin 2FA authentication workflow:
        1. Login does not return tokens but indicates 2FA is required.
        2. OTP is verified to return access and refresh tokens.
        3. Token rotation and blacklisting work for super-admin tokens as well.
        """
        # 1. Login attempt
        login_url = reverse('login')
        data = {
            'email': self.sa.email,
            'password': self.sa_password
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['require_2fa'])
        self.assertNotIn('data', response.data) # No tokens should be returned yet

        # Retrieve the generated OTP from DB
        otp_record = SuperAdminOTP.objects.filter(user=self.sa).latest('created_at')
        otp_code = otp_record.otp_code

        # 2. Verify OTP to get tokens
        verify_url = reverse('verify-otp')
        verify_data = {
            'email': self.sa.email,
            'otp_code': otp_code
        }
        verify_response = self.client.post(verify_url, verify_data)
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['success'])
        
        sa_access = verify_response.data['data']['access']
        sa_refresh = verify_response.data['data']['refresh']
        self.assertIsNotNone(sa_access)
        self.assertIsNotNone(sa_refresh)

        # 3. Test rotation on super-admin refresh token
        refresh_url = reverse('token-refresh')
        refresh_data = {'refresh': sa_refresh}
        
        refresh_response = self.client.post(refresh_url, refresh_data)
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        new_sa_access = refresh_response.data.get('access')
        new_sa_refresh = refresh_response.data.get('refresh')
        self.assertIsNotNone(new_sa_access)
        self.assertIsNotNone(new_sa_refresh)
        self.assertNotEqual(sa_access, new_sa_access)
        self.assertNotEqual(sa_refresh, new_sa_refresh)

        # 4. Old super-admin refresh token should now be blacklisted
        failed_refresh_response = self.client.post(refresh_url, refresh_data)
        self.assertEqual(failed_refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(failed_refresh_response.data['success'])
        self.assertEqual(failed_refresh_response.data['message'], 'Token is blacklisted')
