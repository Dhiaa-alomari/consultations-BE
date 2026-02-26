from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from decimal import Decimal

from consultations.models import ConsultationCategory, Appointment
from consultations.serializers import (
    ConsultationCategorySerializer,
    AppointmentSerializer,
    CreateAppointmentSerializer,
)

User = get_user_model()


class MockRequest:
    """Simple mock request object with user attribute."""
    def __init__(self, user):
        self.user = user


class ConsultationCategorySerializerTest(TestCase):
    """Test ConsultationCategorySerializer."""

    def setUp(self):
        """Set up test data."""
        self.category_data = {
            'category': 'Immigration',
            'price_per_15min': '45.00',
            'description': 'Immigration advice'
        }

    def test_serializer_with_valid_data(self):
        """Test serializer accepts valid data."""
        serializer = ConsultationCategorySerializer(data=self.category_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_serializer_creates_category(self):
        """Test serializer creates category correctly."""
        serializer = ConsultationCategorySerializer(data=self.category_data)
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.category, 'Immigration')
        self.assertEqual(category.price_per_15min, Decimal('45.00'))
        self.assertEqual(category.description, 'Immigration advice')

    def test_serializer_with_missing_required_field(self):
        """Test serializer rejects data missing required fields."""
        data = {'category': 'Immigration'}  # Missing price_per_15min
        serializer = ConsultationCategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price_per_15min', serializer.errors)

    def test_serializer_read_returns_all_fields(self):
        """Test serializer returns id, category, price, description on read."""
        category = ConsultationCategory.objects.create(**self.category_data)
        serializer = ConsultationCategorySerializer(category)
        self.assertIn('id', serializer.data)
        self.assertIn('category', serializer.data)
        self.assertIn('price_per_15min', serializer.data)
        self.assertIn('description', serializer.data)


class AppointmentSerializerTest(TestCase):
    """Test AppointmentSerializer (read-only)."""

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
        self.appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )

    def test_serializer_contains_all_fields(self):
        """Test serializer exposes all required fields."""
        serializer = AppointmentSerializer(self.appointment)
        data = serializer.data
        self.assertIn('id', data)
        self.assertIn('category', data)
        self.assertIn('category_name', data)
        self.assertIn('price_per_15min', data)
        self.assertIn('date', data)
        self.assertIn('time', data)
        self.assertIn('duration', data)
        self.assertIn('total_price', data)
        self.assertIn('is_paid', data)
        self.assertIn('created_at', data)

    def test_category_name_from_related_object(self):
        """Test category_name is populated from category.category."""
        serializer = AppointmentSerializer(self.appointment)
        self.assertEqual(serializer.data['category_name'], 'Immigration')

    def test_total_price_is_computed(self):
        """Test total_price is exposed and computed correctly."""
        serializer = AppointmentSerializer(self.appointment)
        self.assertEqual(serializer.data['total_price'], '180.00')


class CreateAppointmentSerializerTest(TestCase):
    """Test CreateAppointmentSerializer validation."""

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
        self.valid_data = {
            'category': self.category.id,
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'time': '10:00:00',
            'duration': 60
        }

    # ─── Valid Data Tests ─────────────────────────────────────────────────────

    def test_valid_appointment_data(self):
        """Test serializer accepts completely valid appointment data."""
        serializer = CreateAppointmentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_all_duration_choices_accepted(self):
        """Test all valid duration choices (15, 30, 60, 120) are accepted."""
        for duration in [15, 30, 60, 120]:
            data = self.valid_data.copy()
            data['duration'] = duration
            serializer = CreateAppointmentSerializer(data=data)
            self.assertTrue(
                serializer.is_valid(),
                f"Duration {duration} should be valid but got: {serializer.errors}"
            )

    # ─── Date Validation Tests ────────────────────────────────────────────────

    def test_reject_past_date(self):
        """Test serializer rejects dates in the past."""
        data = self.valid_data.copy()
        data['date'] = '2020-01-01'
        serializer = CreateAppointmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('date', serializer.errors)
        self.assertIn('past', str(serializer.errors['date'][0]).lower())

    def test_accept_today_date(self):
        """Test serializer accepts today's date."""
        data = self.valid_data.copy()
        data['date'] = date.today().isoformat()
        serializer = CreateAppointmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_accept_future_date(self):
        """Test serializer accepts future dates."""
        data = self.valid_data.copy()
        data['date'] = (date.today() + timedelta(days=30)).isoformat()
        serializer = CreateAppointmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # ─── Time Validation Tests ────────────────────────────────────────────────

    def test_reject_time_before_9am(self):
        """Test serializer rejects appointments before 9:00 AM."""
        for hour in [0, 6, 8]:
            data = self.valid_data.copy()
            data['time'] = f'{hour:02d}:00:00'
            serializer = CreateAppointmentSerializer(data=data)
            self.assertFalse(
                serializer.is_valid(),
                f"Time {hour}:00 should be rejected"
            )
            self.assertIn('time', serializer.errors)

    def test_reject_time_at_or_after_6pm(self):
        """Test serializer rejects appointments at or after 6:00 PM."""
        for hour in [18, 19, 20, 23]:
            data = self.valid_data.copy()
            data['time'] = f'{hour:02d}:00:00'
            serializer = CreateAppointmentSerializer(data=data)
            self.assertFalse(
                serializer.is_valid(),
                f"Time {hour}:00 should be rejected"
            )
            self.assertIn('time', serializer.errors)

    def test_accept_time_9am(self):
        """Test serializer accepts 9:00 AM exactly."""
        data = self.valid_data.copy()
        data['time'] = '09:00:00'
        serializer = CreateAppointmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_accept_times_within_working_hours(self):
        """Test serializer accepts all times between 9 AM and 6 PM."""
        for hour in [9, 10, 11, 12, 13, 14, 15, 16, 17]:
            data = self.valid_data.copy()
            data['time'] = f'{hour:02d}:00:00'
            data['duration'] = 15  # Short to avoid end-time issues
            serializer = CreateAppointmentSerializer(data=data)
            self.assertTrue(
                serializer.is_valid(),
                f"Time {hour}:00 should be valid but got: {serializer.errors}"
            )

    # ─── Duration Validation Tests ────────────────────────────────────────────

    def test_reject_invalid_duration(self):
        """Test serializer rejects invalid durations."""
        for invalid in [0, 10, 45, 90, 150, 200]:
            data = self.valid_data.copy()
            data['duration'] = invalid
            serializer = CreateAppointmentSerializer(data=data)
            self.assertFalse(
                serializer.is_valid(),
                f"Duration {invalid} should be rejected"
            )
            self.assertIn('duration', serializer.errors)

    # ─── End Time Validation Tests ────────────────────────────────────────────

    def test_reject_appointment_ending_after_6pm(self):
        """Test serializer rejects appointments that would end after 6:00 PM."""
        data = self.valid_data.copy()
        data['time'] = '17:00:00'
        data['duration'] = 120  # Would end at 19:00
        serializer = CreateAppointmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('6:00 PM', str(serializer.errors['non_field_errors'][0]))

    def test_reject_appointment_ending_exactly_at_6pm(self):
        """Test serializer rejects appointments ending exactly at 6:00 PM."""
        data = self.valid_data.copy()
        data['time'] = '16:00:00'
        data['duration'] = 120  # Ends exactly at 18:00
        serializer = CreateAppointmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_accept_appointment_ending_before_6pm(self):
        """Test serializer accepts appointments ending before 6:00 PM."""
        data = self.valid_data.copy()
        data['time'] = '16:00:00'
        data['duration'] = 60  # Ends at 17:00
        serializer = CreateAppointmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # ─── Double Booking Tests ─────────────────────────────────────────────────

    def test_reject_double_booking_same_slot(self):
        """Test serializer rejects booking same category/date/time twice."""
        # Create first appointment
        Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration=60
        )
        # Try to book same slot
        serializer = CreateAppointmentSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        # Check for either custom validation message or database unique constraint message
        error_msg = str(serializer.errors).lower()
        self.assertTrue(
            'already booked' in error_msg or 'unique' in error_msg,
            f"Expected 'already booked' or 'unique' in error message, got: {serializer.errors}"
        )

    def test_allow_different_category_same_time(self):
        """Test serializer allows same time/date for different category."""
        other_category = ConsultationCategory.objects.create(
            category='Family Law',
            price_per_15min=Decimal('60.00')
        )
        # Create first appointment
        Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            duration=60
        )
        # Book different category, same slot — should succeed
        data = self.valid_data.copy()
        data['category'] = other_category.id
        serializer = CreateAppointmentSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    # ─── Creation Tests ───────────────────────────────────────────────────────

    def test_create_appointment_attaches_user(self):
        """Test serializer.create() attaches user from context."""
        mock_request = MockRequest(self.user)
        
        serializer = CreateAppointmentSerializer(
            data=self.valid_data,
            context={'request': mock_request}
        )
        self.assertTrue(serializer.is_valid())
        appointment = serializer.save()
        self.assertEqual(appointment.user, self.user)

    def test_create_appointment_computes_price(self):
        """Test created appointment has correct computed price."""
        mock_request = MockRequest(self.user)
        
        serializer = CreateAppointmentSerializer(
            data=self.valid_data,
            context={'request': mock_request}
        )
        self.assertTrue(serializer.is_valid())
        appointment = serializer.save()
        self.assertEqual(appointment.total_price, Decimal('180.00'))