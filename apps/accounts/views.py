from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import CustomTokenObtainPairSerializer, StaffUserSerializer, ChangePasswordSerializer
from .permissions import IsAdminOrManager

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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
