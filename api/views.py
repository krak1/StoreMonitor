import os
import random
import string

from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .signals import start_report_generation
from django.core.cache import cache


class TriggerReportView(APIView):

    def post(self, request):
        # Trigger report generation here and return a report_id
        report_id = generate_random_code()

        start_report_generation.send(sender=TriggerReportView, report_id=report_id)

        cache.set(report_id, False)

        return Response({'report_id': report_id})


class GetReportView(APIView):
    def get(self, request):
        report_id = request.GET.get('report_id')
        if cache.get(report_id):

            file_path = '/report/+' + report_id + '.csv'

            if os.path.exists(file_path):
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                response['Content-Disposition'] = 'attachment; filename="'+report_id+'.csv"'
                return response

        return Response({'status': 'Running'})


def generate_random_code():
    length = 6
    code = ''.join(random.choices(string.ascii_uppercase, k=length))
    return code

