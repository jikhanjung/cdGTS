"""User admin serializers (staff-only user management + memberships)."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Membership

User = get_user_model()


class MembershipSerializer(serializers.ModelSerializer):
    authority = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    authority_name = serializers.CharField(source="authority.name", read_only=True)
    kind = serializers.CharField(source="authority.kind", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "authority", "authority_name", "kind", "role"]


class UserSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)
    can_ratify = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email",
                  "is_staff", "is_active", "date_joined", "memberships", "can_ratify"]
        read_only_fields = ["username", "date_joined"]

    def get_can_ratify(self, obj):
        from .permissions import can_ratify
        return can_ratify(obj)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "first_name", "last_name", "email", "is_staff", "is_active"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
