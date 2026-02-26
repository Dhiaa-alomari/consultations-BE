from django.test import TestCase
from django.contrib.auth import get_user_model
from datetime import date, time
from decimal import Decimal

from consultations.models import ConsultationCategory, Appointment

User = get_user_model()


class ConsultationCategoryModelTest(TestCase):
    """Test ConsultationCategory model."""

    def setUp(self):
        """Set up test data."""
        self.category = ConsultationCategory.objects.create(
            category='Immigration',
            price_per_15min=Decimal('45.00'),
            description='Immigration legal advice'
        )

    def test_category_creation(self):
        """Test category is created correctly."""
        self.assertEqual(self.category.category, 'Immigration')
        self.assertEqual(self.category.price_per_15min, Decimal('45.00'))
        self.assertEqual(self.category.description, 'Immigration legal advice')

    def test_category_str_method(self):
        """Test __str__ returns correct display value."""
        self.assertEqual(str(self.category), 'Immigration')

    def test_category_ordering(self):
        """Test categories are ordered by category name."""
        ConsultationCategory.objects.create(
            category='Felonies',
            price_per_15min=Decimal('50.00')
        )
        categories = list(ConsultationCategory.objects.all())
        self.assertEqual(categories[0].category, 'Felonies')
        self.assertEqual(categories[1].category, 'Immigration')

    def test_category_choices_validation(self):
        """Test category must be one of the predefined choices."""
        # Valid choice
        valid_category = ConsultationCategory(
            category='Family Law',
            price_per_15min=Decimal('60.00')
        )
        valid_category.full_clean()  # Should not raise
        valid_category.save()
        self.assertEqual(valid_category.category, 'Family Law')

    def test_price_precision(self):
        """Test price_per_15min accepts correct decimal precision."""
        category = ConsultationCategory.objects.create(
            category='Tax Consulting',
            price_per_15min=Decimal('65.50')
        )
        self.assertEqual(category.price_per_15min, Decimal('65.50'))


class AppointmentModelTest(TestCase):
    """Test Appointment model."""

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

    def test_appointment_creation(self):
        """Test appointment is created correctly with all fields."""
        appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        self.assertEqual(appointment.user, self.user)
        self.assertEqual(appointment.category, self.category)
        self.assertEqual(appointment.date, date(2026, 4, 10))
        self.assertEqual(appointment.time, time(10, 0))
        self.assertEqual(appointment.duration, 60)
        self.assertFalse(appointment.is_paid)
        self.assertIsNotNone(appointment.created_at)

    def test_compute_price_15min(self):
        """Test price calculation for 15-minute session."""
        appointment = Appointment(
            user=self.user,
            category=self.category,
            duration=15
        )
        expected = Decimal('45.00')
        self.assertEqual(appointment.compute_price(), expected)

    def test_compute_price_30min(self):
        """Test price calculation for 30-minute session."""
        appointment = Appointment(
            user=self.user,
            category=self.category,
            duration=30
        )
        expected = Decimal('90.00')
        self.assertEqual(appointment.compute_price(), expected)

    def test_compute_price_60min(self):
        """Test price calculation for 60-minute session."""
        appointment = Appointment(
            user=self.user,
            category=self.category,
            duration=60
        )
        expected = Decimal('180.00')
        self.assertEqual(appointment.compute_price(), expected)

    def test_compute_price_120min(self):
        """Test price calculation for 120-minute session."""
        appointment = Appointment(
            user=self.user,
            category=self.category,
            duration=120
        )
        expected = Decimal('360.00')
        self.assertEqual(appointment.compute_price(), expected)

    def test_compute_price_different_base_price(self):
        """Test price calculation with different base price_per_15min."""
        expensive_category = ConsultationCategory.objects.create(
            category='Intellectual Property',
            price_per_15min=Decimal('75.00')
        )
        appointment = Appointment(
            user=self.user,
            category=expensive_category,
            duration=60
        )
        expected = Decimal('300.00')  # 75 * 4 = 300
        self.assertEqual(appointment.compute_price(), expected)

    def test_total_price_saved_on_create(self):
        """Test total_price is computed and saved automatically on creation."""
        appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        self.assertEqual(appointment.total_price, Decimal('180.00'))

    def test_total_price_updated_on_save(self):
        """Test total_price is recomputed when duration changes."""
        appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        # Change duration
        appointment.duration = 30
        appointment.save()
        self.assertEqual(appointment.total_price, Decimal('90.00'))

    def test_unique_together_constraint(self):
        """Test (category, date, time) uniqueness constraint prevents double booking."""
        Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        # Attempt to book same slot
        with self.assertRaises(Exception):
            Appointment.objects.create(
                user=self.user,
                category=self.category,
                date=date(2026, 4, 10),
                time=time(10, 0),
                duration=30
            )

    def test_different_category_same_time_allowed(self):
        """Test same date/time but different category is allowed."""
        other_category = ConsultationCategory.objects.create(
            category='Family Law',
            price_per_15min=Decimal('60.00')
        )
        Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        # Different category, same slot — should succeed
        appointment2 = Appointment.objects.create(
            user=self.user,
            category=other_category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        self.assertIsNotNone(appointment2.pk)

    def test_appointment_str_method(self):
        """Test __str__ returns readable representation."""
        appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        expected = 'testuser | Immigration | 2026-04-10 10:00:00 | 60min | Unpaid'
        self.assertEqual(str(appointment), expected)

    def test_is_paid_default_false(self):
        """Test is_paid defaults to False."""
        appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        self.assertFalse(appointment.is_paid)

    def test_is_paid_can_be_set_true(self):
        """Test is_paid can be set to True (after payment)."""
        appointment = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60,
            is_paid=True
        )
        self.assertTrue(appointment.is_paid)

    def test_appointment_ordering(self):
        """Test appointments are ordered by date DESC, time DESC."""
        appt1 = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 10),
            time=time(10, 0),
            duration=60
        )
        appt2 = Appointment.objects.create(
            user=self.user,
            category=self.category,
            date=date(2026, 4, 11),
            time=time(14, 0),
            duration=30
        )
        appointments = list(Appointment.objects.all())
        self.assertEqual(appointments[0].pk, appt2.pk)  # Most recent first
        self.assertEqual(appointments[1].pk, appt1.pk)
