from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class LoginView(TokenObtainPairView):
    pass


class RefreshView(TokenRefreshView):
    pass


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # For JWT, client discards token; optionally implement blacklist if needed
    return Response({'detail': 'Logged out'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({'username': user.username, 'email': user.email, 'is_staff': user.is_staff, 'is_superuser': user.is_superuser})
