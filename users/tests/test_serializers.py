# tests/test_serializers.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from unittest.mock import patch, MagicMock
from ..serializers import (
    RegisterSerializer,
    UserSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer
)
from ..models import Profile

User = get_user_model()

class RegisterSerializerTests(TestCase):
    """Tests for the registration serializer."""
    
    def setUp(self):
        self.valid_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!'
        }
    
    def test_valid_registration_data(self):
        """Test valid registration data"""
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_passwords_must_match(self):
        """Test that passwords must match"""
        data = self.valid_data.copy()
        data['password_confirm'] = 'DifferentPass123!'
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)
    
    def test_email_unique_validation(self):
        """Test email uniqueness validation"""
        # Create a user with the same email
        User.objects.create_user(
            username='existing',
            email='new@example.com',
            password='TestPass123!'
        )
        
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)
    
    def test_username_unique_validation(self):
        """Test username uniqueness validation"""
        User.objects.create_user(
            username='newuser',
            email='other@example.com',
            password='TestPass123!'
        )
        
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
    
    @patch('users.serializers._run_django_password_validators')  # Modify the path
    def test_password_validators_called(self, mock_validators):
        """Test that password validators are called"""
        serializer = RegisterSerializer(data=self.valid_data)
        serializer.is_valid()
        mock_validators.assert_called_once_with('StrongPass123!')
    
    def test_password_uniqueness_check(self):
        """Test password uniqueness check"""
        # Create a user with a known password
        User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='CommonPass123!'
        )
        
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'CommonPass123!',
            'password_confirm': 'CommonPass123!'
        }
        
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)
    
    def test_create_user_with_profile(self):
        """Test creating a user with a profile"""
        serializer = RegisterSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('StrongPass123!'))
        
        # that the profile is created
        self.assertTrue(hasattr(user, 'profile'))
        self.assertIsInstance(user.profile, Profile)


class ProfileSerializerTests(TestCase):
    """Test cases for the profile serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )

        self.profile = Profile.objects.create(user=self.user)
    
    def test_profile_serializer_fields(self):
        """Test the fields of the profile serializer"""
        serializer = ProfileSerializer(instance=self.profile)
        data = serializer.data
        
        self.assertIn('avatar_url', data)
        self.assertIn('phone', data)
        self.assertIn('bio', data)
        self.assertNotIn('avatar', data)  # write_only
    
    def test_avatar_url_method(self):
        """Test the avatar_url method"""
        serializer = ProfileSerializer(instance=self.profile)
        url = serializer.get_avatar_url(self.profile)
        self.assertIsNotNone(url)
    
    def test_avatar_url_without_avatar(self):
        """Test avatar_url method when no avatar is present"""
        self.profile.avatar = None
        self.profile.save()
        serializer = ProfileSerializer(instance=self.profile)
        url = serializer.get_avatar_url(self.profile)
        self.assertIsNone(url)


class UserSerializerTests(TestCase):
    """Test cases for the user serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='TestPass123!'
        )
        # Create manually the profile for the user
        Profile.objects.create(user=self.user)
    
    def test_user_serializer_fields(self):
        """Test the fields of the user serializer"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        expected_fields = ['id', 'username', 'email', 'first_name', 
                          'last_name', 'is_staff', 'date_joined', 'profile']
        
        for field in expected_fields:
            self.assertIn(field, data)
        
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
    
    def test_read_only_fields(self):
        """"Test read-only fields in the user serializer"""
        read_only_fields = UserSerializer.Meta.read_only_fields
        self.assertIn('id', read_only_fields)
        self.assertIn('is_staff', read_only_fields)
        self.assertIn('date_joined', read_only_fields)


class ProfileUpdateSerializerTests(TestCase):
    """Test update serializers for the profile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Original',
            last_name='User',
            password='TestPass123!'
        )
        # Create profile manually
        self.profile = Profile.objects.create(
            user=self.user,
            phone='',
            bio=''
        )
        self.factory = APIRequestFactory()
    
    def test_update_user_fields(self):
        """Test creating user's fileds"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        serializer = ProfileUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.update(self.user, serializer.validated_data)
        
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
    
    def test_update_profile_fields(self):
        """Test Updating all profile's fileld"""
        data = {
            'phone': '9876543210',
            'bio': 'This is an updated bio'
        }
        
        serializer = ProfileUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.update(self.user, serializer.validated_data)
        
        # update the profile from database
        updated_user.profile.refresh_from_db()
        self.assertEqual(updated_user.profile.phone, '9876543210')
        self.assertEqual(updated_user.profile.bio, 'This is an updated bio')
    
    def test_partial_update(self):
        """Test part of updating"""
        data = {
            'first_name': 'OnlyFirstName'
        }
        
        serializer = ProfileUpdateSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        original_last_name = self.user.last_name
        original_phone = self.user.profile.phone
        
        updated_user = serializer.update(self.user, serializer.validated_data)
        
        self.assertEqual(updated_user.first_name, 'OnlyFirstName')
        self.assertEqual(updated_user.last_name, original_last_name)  # Not change 
        self.assertEqual(updated_user.profile.phone, original_phone)  # Not change


class ChangePasswordSerializerTests(TestCase):
    
    """Tests for the change password serializer"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='OldPass123!'
        )
        # Create profile manually (not required but for consistency)
        Profile.objects.create(user=self.user)
        
        self.factory = APIRequestFactory()
        self.request = self.factory.post('/')
        self.request.user = self.user
        
        self.valid_data = {
            'old_password': 'OldPass123!',
            'new_password': 'NewStrongPass123!',
            'confirm_password': 'NewStrongPass123!'
        }
    
    def test_valid_password_change(self):
        
        """Tests for valid password change"""
        serializer = ChangePasswordSerializer(
            data=self.valid_data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
    
    def test_old_password_incorrect(self):
        """Tests for incorrect old password"""
        data = self.valid_data.copy()
        data['old_password'] = 'WrongPass123!'
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('old_password', serializer.errors)
    
    def test_new_passwords_mismatch(self):
        """Tests for mismatched new passwords"""
        data = self.valid_data.copy()
        data['confirm_password'] = 'DifferentPass123!'
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('confirm_password', serializer.errors)
    
    def test_new_password_same_as_old(self):
        """Tests for new password being the same as the old password"""
        data = self.valid_data.copy()
        data['new_password'] = 'OldPass123!'
        data['confirm_password'] = 'OldPass123!'
        
        serializer = ChangePasswordSerializer(
            data=data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)
    
    def test_password_uniqueness_check(self):
        """Tests for password uniqueness check"""
        # Create another user with the same new password
        User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='NewStrongPass123!'
        )
        
        serializer = ChangePasswordSerializer(
            data=self.valid_data,
            context={'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('new_password', serializer.errors)
    
    def test_save_method(self):
        """Tests for the save method"""
        serializer = ChangePasswordSerializer(
            data=self.valid_data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        
        result = serializer.save()
        
        self.assertEqual(result, self.user)
        
        # Verification of password change
        updated_user = User.objects.get(pk=self.user.pk)
        self.assertTrue(updated_user.check_password('NewStrongPass123!'))