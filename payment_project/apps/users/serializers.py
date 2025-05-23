from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from .models import User # Using the custom User model from apps.users.models

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        # Hash the password before saving
        validated_data['password_hash'] = make_password(validated_data.pop('password'))
        user = User.objects.create(**validated_data)
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.password_hash = make_password(validated_data.pop('password'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Customize the output representation to exclude password_hash.
        """
        ret = super().to_representation(instance)
        # The custom User model has 'password_hash', not 'password' directly in the model
        # So, we don't need to pop 'password' from ret if it's not defined in fields for output.
        # If 'password_hash' was included in Meta.fields for output, we would pop it here.
        # Since 'password_hash' is not in Meta.fields by default for read, it's fine.
        # 'password' field is write_only, so it won't be in ret.
        return ret

class UserDisplaySerializer(serializers.ModelSerializer):
    """
    Serializer for displaying user information, excluding sensitive details.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'created_at', 'updated_at')
        read_only_fields = fields # All fields are read-only in this context
