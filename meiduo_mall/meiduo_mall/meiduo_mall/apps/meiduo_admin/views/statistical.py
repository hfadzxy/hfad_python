from rest_framework.response import Response
from datetime import date
from users.models import User
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser

class UserTotalCountView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        now_date = date.today()
        count = User.objects.all().count()
        return Response({
            'count':count,
            'date':now_date
        })