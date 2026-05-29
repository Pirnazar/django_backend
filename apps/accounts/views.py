from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import (
    CustomTokenObtainPairSerializer, StaffUserSerializer,
    ChangePasswordSerializer, ClientRegisterSerializer,
)
from .permissions import IsAdminOrManager

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ClientRegisterView(APIView):
    """POST /api/v1/auth/register/ — self-registration for clients (mobile app)."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = CustomTokenObtainPairSerializer.get_token(user)
        client = getattr(user, 'client_profile', None)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'token_type': 'Bearer',
                'client_code': client.client_code if client else None,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
            },
            status=status.HTTP_201_CREATED,
        )

class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = StaffUserSerializer(request.user)
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'password set'})

class StaffUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = StaffUserSerializer
    permission_classes = [IsAdminOrManager]
    search_fields = ['email', 'full_name', 'phone_number']
    filterset_fields = ['role', 'is_active']
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
        if self.request.user.role == 'superadmin':
            return self.queryset
        return self.queryset.exclude(role='superadmin')
