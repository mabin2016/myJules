from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from .models import User # Using the custom User model
from .serializers import UserSerializer, UserDisplaySerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    Primarily for user creation (registration).
    """
    queryset = User.objects.all().order_by('-created_at')
    # serializer_class = UserSerializer # Default serializer

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSerializer
        # For list/retrieve, use a more restrictive serializer if needed,
        # or ensure UserSerializer correctly handles output representation.
        # Using UserDisplaySerializer for read actions to ensure password_hash is not exposed.
        return UserDisplaySerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Allow anyone to create a user (register)
            self.permission_classes = [permissions.AllowAny]
        else:
            # For other actions (list, retrieve, update, delete), require authentication.
            # Further, only admin should probably list all users or delete/update arbitrary users.
            # For simplicity here, IsAuthenticated is used.
            # A more granular permission system would be needed for production.
            self.permission_classes = [permissions.IsAuthenticated] # Or IsAdminUser for list/destroy
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Return the UserDisplaySerializer to avoid exposing password hash in response
            display_serializer = UserDisplaySerializer(user, context={'request': request})
            headers = self.get_success_headers(display_serializer.data)
            return Response(display_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Disabling other actions for this simple ViewSet if it's only for registration and admin use
    # For example, a regular user should not be able to list all users.
    # Adjust actions based on requirements. If it's purely for registration,
    # a CreateAPIView might be more appropriate.
    # For this task, we'll assume ModelViewSet is used but list/retrieve might be admin-only.
    
    # If regular users can retrieve/update their own info:
    # def get_queryset(self):
    #     if self.request.user.is_staff:
    #         return User.objects.all()
    #     elif self.request.user.is_authenticated:
    #         return User.objects.filter(pk=self.request.user.pk)
    #     return User.objects.none()

    # def check_object_permissions(self, request, obj):
    #     super().check_object_permissions(request, obj)
    #     if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
    #         if not request.user.is_staff and obj != request.user:
    #             self.permission_denied(
    #                 request, message='You do not have permission to access this user.'
    #             )
