from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.health import run_all_checks


class HealthView(APIView):
    """存活探测（轻量），供 Compose healthcheck / 负载均衡探活使用。"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok', 'service': 'ncbcnet'})


class HealthComponentsView(APIView):
    """组件级健康状态（公开，仅暴露状态与友好说明，不泄露内部细节）。"""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(run_all_checks())
