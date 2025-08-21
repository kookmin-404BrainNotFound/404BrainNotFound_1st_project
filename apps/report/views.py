from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import ReportRun, DangerCheckList

# Create your views here.


class StartReportView(APIView):
    def post(self, request):
        # Create a new ReportRun instance
        report_run = ReportRun.objects.create()
        return Response({'report_run_id': report_run.id}, status=status.HTTP_201_CREATED)


class DangerCheckListView(APIView):
    @swagger_auto_schema(
        operation_description="Create or retrieve danger checklists for a report run",
        manual_parameters=[
            openapi.Parameter('report_run_id', openapi.IN_PATH, description="ID of the ReportRun", type=openapi.TYPE_INTEGER),
            openapi.Parameter('description', openapi.IN_QUERY, description="Description of the danger checklist", type=openapi.TYPE_STRING)
        ],
        responses={
            201: openapi.Response('Danger checklist created', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'danger_checklist_id': openapi.Schema(type=openapi.TYPE_INTEGER)})),
            200: openapi.Response('Danger checklists retrieved', openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'id': openapi.Schema(type=openapi.TYPE_INTEGER), 'description': openapi.Schema(type=openapi.TYPE_STRING)}))),
            404: 'ReportRun not found'
        }
    )
    def post(self, request, report_run_id):
        try:
            report_run = ReportRun.objects.get(id=report_run_id)
        except ReportRun.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)

        description = request.data.get('description', '')
        danger_checklist = DangerCheckList.objects.create(report_run=report_run, description=description)
        return Response({'danger_checklist_id': danger_checklist.id}, status=status.HTTP_201_CREATED)
    
    def get(self, request, report_run_id):
        try:
            report_run = ReportRun.objects.get(id=report_run_id)
        except ReportRun.DoesNotExist:
            return Response({'error': 'ReportRun not found'}, status=status.HTTP_404_NOT_FOUND)

        checklists = report_run.danger_checklists.all()
        data = [{'id': checklist.id, 'description': checklist.description} for checklist in checklists]
        return Response(data, status=status.HTTP_200_OK)
    
    