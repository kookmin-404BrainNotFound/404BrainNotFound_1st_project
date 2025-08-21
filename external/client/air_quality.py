#
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status, permissions
# from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
#
# from external.client.seoul_data import AirQualityClient   # 만든 클라이언트 경로에 맞게 수정
# from external.client.base import HTTPError               # 예외 클래스 경로에 맞게 수정
#
#
# class AirQualityView(APIView):
#     permission_classes = [permissions.AllowAny]   # 인증이 필요하다면 IsAuthenticated로 바꾸세요
#
#     @extend_schema(
#         summary="실시간 대기질(구별) 조회",
#         description="서울 열린데이터 광장의 RealtimeCityAir를 프록시하여 반환합니다.",
#         parameters=[
#             OpenApiParameter(name="gu", description="구 이름(예: 강남구)", required=False, type=OpenApiTypes.STR),
#             OpenApiParameter(name="size", description="가져올 개수(기본 25)", required=False, type=OpenApiTypes.INT),
#         ],
#         responses={200: OpenApiTypes.OBJECT},
#         tags=["airquality"],   # Swagger 분류 탭
#     )
#     def get(self, request):
#         gu = request.query_params.get("gu")
#         try:
#             size = int(request.query_params.get("size", 25))
#         except ValueError:
#             return Response({"detail": "size는 정수여야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
#
#         client = AirQualityClient()
#         try:
#             data = client.get_realtime_city_air(size=size, gu_name=gu)
#             return Response(data, status=status.HTTP_200_OK)
#         except HTTPError as e:
#             # 외부 API 오류는 502 정도로 매핑
#             return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
#         finally:
#             client.close()
