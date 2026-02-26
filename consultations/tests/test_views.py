from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date, time, timedelta
from decimal import Decimal

from consultations.models import ConsultationCategory, Appointment

User = get_user_model()


class CategoryListViewTest(APITestCase):
    """Test CategoryListView (public endpoint)."""

    def setUp(self):
        """Set up test data."""
        self.url = reverse('category_list')
        self.category1 = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00'),
            description='Immigration legal advice'
        )
        self.category2 = ConsultationCategory.objects.create(
            category='Felonies',
            price_per_15min=Decimal('50.00'),
            description='Criminal defense'
        )

    def test_list_categories_no_auth_required(self):
        """Test anyone can list categories without authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_all_categories(self):
        """Test list returns all created categories."""
        response = self.client.get(self.url)
        # Response might be paginated or a plain list
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        self.assertEqual(len(results), 2)

    def test_categories_contain_required_fields(self):
        """Test each category contains id, category, price_per_15min."""
        response = self.client.get(self.url)
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        category = results[0]
        self.assertIn('id', category)
        self.assertIn('category', category)
        self.assertIn('price_per_15min', category)
        self.assertIn('description', category)

    def test_categories_ordered_alphabetically(self):
        """Test categories are ordered by category name."""
        response = self.client.get(self.url)
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        categories = [c['category'] for c in results]
        self.assertEqual(categories, sorted(categories))


class CategoryAdminCreateViewTest(APITestCase):
    """Test CategoryAdminCreateView (admin-only)."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='UserPass123!'
        )
        self.url = reverse('category_create')
        self.valid_data = {
            'category': 'Family Law',
            'price_per_15min': '60.00',
            'description': 'Family law consultations'
        }

    def test_create_requires_authentication(self):
        """Test creating category requires authentication."""
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_admin(self):
        """Test regular users cannot create categories."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_category(self):
        """Test admin can create new categories."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['category'], 'Family Law')
        self.assertEqual(response.data['price_per_15min'], '60.00')

    def test_create_increments_category_count(self):
        """Test creating category increases total count."""
        initial_count = ConsultationCategory.objects.count()
        self.client.force_authenticate(user=self.admin)
        self.client.post(self.url, self.valid_data)
        self.assertEqual(ConsultationCategory.objects.count(), initial_count + 1)


class CategoryAdminDetailViewTest(APITestCase):
    """Test CategoryAdminDetailView (retrieve, update, delete - admin only)."""

    def setUp(self):
        """Set up test data."""
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='UserPass123!'
        )
        self.category = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00')
        )
        self.url = reverse('category_detail', kwargs={'pk': self.category.pk})

    def test_retrieve_category_admin_only(self):
        """Test retrieving category details requires admin."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_category_admin_only(self):
        """Test only admin can update categories."""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {'price_per_15min': '55.00'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(self.url, {'price_per_15min': '55.00'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.price_per_15min, Decimal('55.00'))

    def test_delete_category_admin_only(self):
        """Test only admin can delete categories."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            ConsultationCategory.objects.filter(pk=self.category.pk).exists()
        )


class SlotAvailabilityViewTest(APITestCase):
    """Test SlotAvailabilityView (public endpoint)."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.category = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00')
        )
        self.url = reverse('slot_availability')
        
        # Create appointments
        Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(14, 0),
            duration=30
        )

    def test_availability_no_auth_required(self):
        """Test availability can be checked without authentication."""
        response = self.client.get(self.url, {
            'category': self.category.id,
            'date': '2026-04-10'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_availability_returns_booked_times(self):
        """Test availability returns list of booked times."""
        response = self.client.get(self.url, {
            'category': self.category.id,
            'date': '2026-04-10'
        })
        self.assertIn('booked_times', response.data)
        booked = response.data['booked_times']
        self.assertEqual(len(booked), 2)
        # Times might be returned as time objects or strings
        booked_str = [str(t) if not isinstance(t, str) else t for t in booked]
        self.assertIn('10:00:00', booked_str)
        self.assertIn('14:00:00', booked_str)

    def test_availability_empty_for_free_date(self):
        """Test availability returns empty list when no bookings exist."""
        response = self.client.get(self.url, {
            'category': self.category.id,
            'date': '2026-05-01'
        })
        self.assertEqual(response.data['booked_times'], [])

    def test_availability_requires_category_param(self):
        """Test availability endpoint requires category parameter."""
        response = self.client.get(self.url, {'date': '2026-04-10'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_availability_requires_date_param(self):
        """Test availability endpoint requires date parameter."""
        response = self.client.get(self.url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_availability_requires_both_params(self):
        """Test availability endpoint requires both parameters."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_availability_different_category_different_bookings(self):
        """Test availability is category-specific."""
        other_category = ConsultationCategory.objects.create(
            category='Family Law',
            price_per_15min=Decimal('60.00')
        )
        response = self.client.get(self.url, {
            'category': other_category.id,
            'date': '2026-04-10'
        })
        self.assertEqual(response.data['booked_times'], [])


class AppointmentCreateViewTest(APITestCase):
    """Test AppointmentCreateView."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.category = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00')
        )
        self.url = reverse('appointment_create')
        self.valid_data = {
            'category': self.category.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00:00',
            'duration': 60
        }

    def test_create_requires_authentication(self):
        """Test creating appointment requires authentication."""
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_appointment_success(self):
        """Test authenticated user can create appointment."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_create_returns_full_appointment_data(self):
        """Test create returns complete appointment with computed price."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_data)
        self.assertIn('total_price', response.data)
        self.assertIn('category_name', response.data)
        self.assertIn('is_paid', response.data)

    def test_create_computes_price_server_side(self):
        """Test appointment price is calculated server-side."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.data['total_price'], '180.00')

    def test_create_is_paid_false_by_default(self):
        """Test new appointments are unpaid by default."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.valid_data)
        self.assertFalse(response.data['is_paid'])

    def test_create_increments_appointment_count(self):
        """Test creating appointment increases total count."""
        self.client.force_authenticate(user=self.user)
        initial_count = Appointment.objects.count()
        self.client.post(self.url, self.valid_data)
        self.assertEqual(Appointment.objects.count(), initial_count + 1)

    def test_create_validates_working_hours(self):
        """Test create rejects times outside working hours."""
        self.client.force_authenticate(user=self.user)
        data = self.valid_data.copy()
        data['time'] = '08:00:00'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('time', response.data)

    def test_create_validates_past_date(self):
        """Test create rejects past dates."""
        self.client.force_authenticate(user=self.user)
        data = self.valid_data.copy()
        data['date'] = '2020-01-01'
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)

    def test_create_validates_duration(self):
        """Test create rejects invalid durations."""
        self.client.force_authenticate(user=self.user)
        data = self.valid_data.copy()
        data['duration'] = 45
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', response.data)

    def test_create_prevents_double_booking(self):
        """Test create prevents booking same slot twice."""
        self.client.force_authenticate(user=self.user)
        self.client.post(self.url, self.valid_data)
        response = self.client.post(self.url, self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AppointmentDetailViewTest(APITestCase):
    """Test AppointmentDetailView (retrieve & delete)."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
        self.category = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00')
        )
        self.appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        self.url = reverse('appointment_detail', kwargs={'pk': self.appointment.pk})

    def test_retrieve_requires_authentication(self):
        """Test retrieving appointment requires authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_own_appointment(self):
        """Test user can retrieve their own appointment."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.appointment.id)

    def test_cannot_retrieve_other_user_appointment(self):
        """Test user cannot retrieve another user's appointment."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_requires_authentication(self):
        """Test deleting appointment requires authentication."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_unpaid_appointment(self):
        """Test user can delete their unpaid appointment."""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Appointment.objects.filter(pk=self.appointment.pk).exists()
        )

    def test_cannot_delete_paid_appointment(self):
        """Test user cannot delete paid appointments."""
        self.appointment.is_paid = True
        self.appointment.save()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertTrue(
            Appointment.objects.filter(pk=self.appointment.pk).exists()
        )

    def test_cannot_delete_other_user_appointment(self):
        """Test user cannot delete another user's appointment."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(
            Appointment.objects.filter(pk=self.appointment.pk).exists()
        )

    def test_delete_decrements_appointment_count(self):
        """Test deleting appointment decreases total count."""
        self.client.force_authenticate(user=self.user)
        initial_count = Appointment.objects.count()
        self.client.delete(self.url)
        self.assertEqual(Appointment.objects.count(), initial_count - 1)


class AppointmentHistoryViewTest(APITestCase):
    """Test AppointmentHistoryView (my-appointments)."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='OtherPass123!'
        )
        self.category = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00')
        )
        self.url = reverse('my_appointments')

        # Create appointments for both users
        self.appt1 = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        self.appt2 = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 11),
            time=time(14, 0),
            duration=30
        )
        self.other_appt = Appointment.objects.create(
            user=self.other_user,
            category=self.category,
            date=date(2026, 4, 12),
            time=time(10, 0),
            duration=60
        )

    def test_history_requires_authentication(self):
        """Test my-appointments requires authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_appointments(self):
        """Test user sees only their own appointments, not others'."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle paginated response
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        
        self.assertEqual(len(results), 2)
        appointment_ids = [appt['id'] for appt in results]
        self.assertIn(self.appt1.id, appointment_ids)
        self.assertIn(self.appt2.id, appointment_ids)
        self.assertNotIn(self.other_appt.id, appointment_ids)

    def test_appointments_ordered_by_date_desc(self):
        """Test appointments are ordered by date descending (newest first)."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        
        dates = [appt['date'] for appt in results]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_empty_history_for_new_user(self):
        """Test new user with no appointments gets empty list."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='NewPass123!'
        )
        self.client.force_authenticate(user=new_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        
        self.assertEqual(len(results), 0)

    def test_history_includes_all_appointment_fields(self):
        """Test history includes complete appointment data."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
        
        appt = results[0]
        self.assertIn('id', appt)
        self.assertIn('category_name', appt)
        self.assertIn('date', appt)
        self.assertIn('time', appt)
        self.assertIn('duration', appt)
        self.assertIn('total_price', appt)
        self.assertIn('is_paid', appt)
