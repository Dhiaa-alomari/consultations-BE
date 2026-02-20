from rest_framework import serializers
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import User, Profile


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _run_django_password_validators(password):
    """Run the built-in Django password validators."""
    try:
        validate_password(password)
    except DjangoValidationError as e:
        raise serializers.ValidationError({'password': list(e.messages)})


# ─── Register ─────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value.lower()

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('This username is already taken.')
        return value

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})

        _run_django_password_validators(data['password'])

        # Business rule: no two users may share the same raw password.
        # We iterate only active users — acceptable for small-to-medium user bases.
        raw = data['password']
        for u in User.objects.all():
            if check_password(raw, u.password):
                raise serializers.ValidationError(
                    {'password': 'This password is already used by another account. '
                                 'Please choose a unique password.'}
                )
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user)
        return user


# ─── Profile ──────────────────────────────────────────────────────────────────

class ProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model  = Profile
        fields = ('avatar', 'avatar_url', 'phone', 'bio')
        extra_kwargs = {'avatar': {'write_only': True, 'required': False}}

    def get_avatar_url(self, obj):
        if obj.avatar:
            return str(obj.avatar.url) if hasattr(obj.avatar, 'url') else str(obj.avatar)
        return None


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model  = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_staff', 'date_joined', 'profile')
        read_only_fields = ('id', 'is_staff', 'date_joined')


# ─── Profile Edit (combined user + profile) ──────────────────────────────────

class ProfileUpdateSerializer(serializers.Serializer):
    """Handles updating both User fields and Profile fields in one request."""
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name  = serializers.CharField(required=False, allow_blank=True)
    phone      = serializers.CharField(required=False, allow_blank=True)
    bio        = serializers.CharField(required=False, allow_blank=True)
    avatar     = serializers.ImageField(required=False)

    def update(self, instance, validated_data):
        # Update User fields
        for field in ('first_name', 'last_name'):
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        # Update Profile fields
        profile = instance.profile
        if 'avatar' in validated_data:
            profile.avatar = validated_data['avatar']
        for field in ('phone', 'bio'):
            if field in validated_data:
                setattr(profile, field, validated_data[field])
        profile.save()
        return instance


# ─── Change Password ──────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password     = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        if not user.check_password(data['old_password']):
            raise serializers.ValidationError({'old_password': 'Current password is incorrect.'})

        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'New passwords do not match.'})

        if data['old_password'] == data['new_password']:
            raise serializers.ValidationError(
                {'new_password': 'New password must differ from current password.'}
            )

        _run_django_password_validators(data['new_password'])

        # Uniqueness check
        raw = data['new_password']
        for u in User.objects.exclude(pk=user.pk):
            if check_password(raw, u.password):
                raise serializers.ValidationError(
                    {'new_password': 'This password is already in use by another account.'}
                )

        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
