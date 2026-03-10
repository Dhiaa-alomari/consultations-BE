from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
from ..models import Profile

User = get_user_model()


class RegisterViewTests(APITestCase):
    """"Tests for the registration view"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.valid_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }
    
    def test_register_success(self):
        """Test a successful registration"""
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Verification of creating the user in the database
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        
        # Veification of creating a profile (by serializer)
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_register_missing_fields(self):
        """ Test register with missing fields"""
        data = {'username': 'newuser'}  # without: (email, password)
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
    
    def test_register_duplicate_username(self):
        """Test registration by a repeated user name"""
        # Create user
        User.objects.create_user(
            username='newuser',
            email='existing@example.com',
            password='TestPass123!'
        )
        
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_register_duplicate_email(self):
        """ Test registration by a repeated email"""
        #create user
        User.objects.create_user(
            username='existing',
            email='new@example.com',
            password='TestPass123!'
        )
        
        response = self.client.post(self.register_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class LoginViewTests(APITestCase):
    """Tests log in view """
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('login')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_login_with_username_success(self):
        """Test log in by username successfully"""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_login_with_email_success(self):
        """Test log in by email successfully"""
        data = {
            'username': 'test@example.com',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
    
    def test_login_missing_credentials(self):
        """Test log in without a credential data"""
        data = {}
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_login_invalid_credentials(self):
        """Test log in by a wrong data"""
        data = {
            'username': 'testuser',
            'password': 'WrongPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_nonexistent_user(self):
        """Test log in by an existing user"""
        data = {
            'username': 'nonexistent',
            'password': 'TestPass123!'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTests(APITestCase):
    """Tests logout"""
    
    def setUp(self):
        self.client = APIClient()
        self.logout_url = reverse('logout')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create token when log in
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        
        # Create token on request header 
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_logout_success(self):
        """Test a successful logout"""
        data = {
            'refresh': str(self.refresh)
        }
        
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_logout_without_refresh_token(self):
        """Test logout withiout refresh_token"""
        data = {}
        
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_logout_with_invalid_token(self):
        """Test logout by an invalid token"""
        data = {
            'refresh': 'invalid.token.here'
        }
        
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_logout_unauthenticated(self):
        """Test logout without authentication"""
        self.client.credentials()  # remove token 
        
        data = {
            'refresh': str(self.refresh)
        }
        
        response = self.client.post(self.logout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileViewTests(APITestCase):
    """Tests profile viewing"""
    
    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse('profile')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='TestPass123!'
        )
        
        # create profile manually
        self.profile = Profile.objects.create(
            user=self.user,
            phone='',
            bio=''
        )
        
        # Create token for user
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        
        #create token on request header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_profile_success(self):
        """Test getting on profile successfully"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
        self.assertIn('profile', response.data)
    
    def test_get_profile_unauthenticated(self):
        """Test getting on profile without authentication"""
        self.client.credentials()  # remove token 
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_patch_profile_success(self):
        """Test partly updating for profile successfully"""
        data = {
            'first_name': 'Updated',
            'phone': '1234567890',
            'bio': 'This is my bio'
        }
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        
        # Verification of database updating
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.profile.phone, '1234567890')
        self.assertEqual(self.user.profile.bio, 'This is my bio')
    
    def test_put_profile_success(self):
        """Test full updating for profile successfully"""
        data = {
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'phone': '9876543210',
            'bio': 'New bio'
        }
        
        response = self.client.put(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vefification of database updating
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'NewFirst')
        self.assertEqual(self.user.last_name, 'NewLast')
        self.assertEqual(self.user.profile.phone, '9876543210')
        self.assertEqual(self.user.profile.bio, 'New bio')
    
    def test_partial_update_only_user_fields(self):
        """ Test some updating  for only user input"""
        original_last_name = self.user.last_name
        original_phone = self.user.profile.phone
        
        data = {
            'first_name': 'OnlyFirst'
        }
        
        response = self.client.patch(self.profile_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'OnlyFirst')
        self.assertEqual(self.user.last_name, original_last_name)
        self.assertEqual(self.user.profile.phone, original_phone)


class ChangePasswordViewTests(APITestCase):
    """ Tests for passowrd view"""
    
    def setUp(self):
        self.client = APIClient()
        self.change_password_url = reverse('change_password')  # correct path_name of urls.py
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123!'
        )
        
        # Create profile
        Profile.objects.create(user=self.user)
        
        #Create token for user
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        
        # Create token on request header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        self.valid_data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewStrongPass123!',
            'confirm_password': 'NewStrongPass123!'
        }
    
    def test_change_password_success(self):
        """ Test for changing password successfully"""
        response = self.client.post(self.change_password_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verification of changing pasword
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass123!'))
    
    def test_change_password_unauthenticated(self):
        """ Test changing password without authentication"""
        self.client.credentials()  # remove token 
        
        response = self.client.post(self.change_password_url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_change_password_wrong_old_password(self):
        """ Test changing password by a wrong current password"""
        data = self.valid_data.copy()
        data['old_password'] = 'WrongPass123!'
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('old_password', response.data)
    
    def test_change_password_mismatch(self):
        """ Test changing password with no match both inputed passwords"""
        data = self.valid_data.copy()
        data['confirm_password'] = 'DifferentPass123!'
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)
    
    def test_change_password_same_as_old(self):
        """ Test for changing password likes old password"""
        data = self.valid_data.copy()
        data['new_password'] = 'OldPass123!'
        data['confirm_password'] = 'OldPass123!'
        
        response = self.client.post(self.change_password_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('new_password', response.data)


class DeleteAccountViewTests(APITestCase):
    """ Tests for delete account view """
    
    def setUp(self):
        self.client = APIClient()
        self.delete_url = reverse('delete_account')  # correct path_name urls.py
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        # Create token for user
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        
        # Create token on request header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_delete_account_success(self):
        """ Test remove a user account successfully"""
        data = {
            'password': 'TestPass123!'
        }
        
        response = self.client.delete(self.delete_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        #verification of removing user
        self.assertEqual(User.objects.count(), 0)
    
    def test_delete_account_unauthenticated(self):
        """Test remove a user account without authentication"""
        self.client.credentials()  # remove token 
        
        
        data = {
            'password': 'TestPass123!'
        }
        
        response = self.client.delete(self.delete_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_account_without_password(self):
        """Test remove account without inputed password"""
        data = {}
        
        response = self.client.delete(self.delete_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_delete_account_wrong_password(self):
        """ Test remove a specific user by an wrong password"""
        data = {
            'password': 'WrongPass123!'
        }
        
        response = self.client.delete(self.delete_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Vefifcation of user is not removed
        self.assertEqual(User.objects.count(), 1)