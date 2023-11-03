import os
import random
import string
import asyncio
import threading

from django.http import FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .tasks import start_report_generation_handler
from django.core.cache import cache


class TriggerReportView(APIView):
    def post(self, request):
        # Trigger report generation here and return a report_id
        report_id = generate_random_code()

        def generate_report_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(start_report_generation_handler(report_id=report_id))
            loop.close()
            return result

        threading.Thread(target=generate_report_thread).start()
        print("running asynchronously")

        cache.set(report_id, False)

        return Response({'report_id': report_id})


class GetReportView(APIView):
    def get(self, request):
        report_id = request.GET.get('report_id')

        if cache.get(report_id):

            file_path = 'api/report/' + report_id + '.csv'

            if os.path.exists(file_path):
                response = FileResponse(open(file_path, 'rb'), as_attachment=True)
                response['Content-Disposition'] = 'attachment; filename="' + report_id + '.csv"'
                return response

        return Response({'status': 'Running',
                         'progress': cache.get("items_done"),
                         'report_cache_status': cache.get(report_id)})


def generate_random_code():
    length = 6
    code = ''.join(random.choices(string.ascii_uppercase, k=length))
    return code
