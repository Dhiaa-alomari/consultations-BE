from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from ..models import Profile, DEFAULT_AVATAR

User = get_user_model()

class UserModelTests(TestCase):
    """Testing the custom User model"""

    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
    
    def test_create_user_successfully(self):
        """Test creating a user successfully"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_email_must_be_unique(self):
        """Test that email must be unique"""
        User.objects.create_user(**self.user_data)
        
        duplicate_email_user = {
            'username': 'anotheruser',
            'email': 'test@example.com',
            'password': 'AnotherPass123!'
        }
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_email_user)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.assertTrue(admin_user.is_superuser)
        self.assertTrue(admin_user.is_staff)
    
    def test_user_str_method(self):
        """Test the __str__ method of the User model"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'testuser')
    
    def test_required_fields(self):
        """Test that required fields include email"""
        self.assertIn('email', User.REQUIRED_FIELDS)


class ProfileModelTests(TestCase):
    """Testing the Profile model"""
    
    def setUp(self):
        # Here create only the user, not the profile 
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_profile_creation_manually(self):
        """Test manual profile creation just in testing environment"""
        profile = Profile.objects.create(user=self.user)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone, '')
        self.assertEqual(profile.bio, '')
    
    def test_profile_str_method(self):
        """Test the __str__ method of the Profile model"""
        # Create the profile for this test
        profile = Profile.objects.create(user=self.user)
        expected = f'Profile({self.user.username})'
        self.assertEqual(str(profile), expected)
    
    def test_profile_fields_defaults(self):
        """Test the default values of the Profile model fields"""
        # Create the profile for this test
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(profile.phone, '')
        self.assertEqual(profile.bio, '')
        self.assertEqual(profile.avatar, DEFAULT_AVATAR)
    
    def test_update_profile_fields(self):
        """Test updating profile fields"""
        # Create the profile for this test
        profile = Profile.objects.create(user=self.user)
        profile.phone = '1234567890'
        profile.bio = 'This is a test bio'
        profile.save()
        
        # Retrieve the updated profile from the database
        updated_profile = Profile.objects.get(user=self.user)
        self.assertEqual(updated_profile.phone, '1234567890')
        self.assertEqual(updated_profile.bio, 'This is a test bio')
    
    def test_one_to_one_relationship(self):
        """Test the one-to-one relationship with the user"""
        # Create the profile for this test
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(self.user.profile, profile)  # This will work now that we are creating the profile manually in the test
    
    def test_cannot_create_second_profile_for_same_user(self):
        """Test that a user cannot have more than one profile"""
        # Create the first profile for this test
        Profile.objects.create(user=self.user)
        
        # Try to create a second profile - should fail
        with self.assertRaises(Exception):
            Profile.objects.create(user=self.user)