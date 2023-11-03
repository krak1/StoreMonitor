from rest_framework.views import APIView
from rest_framework.response import Response
from .signals import start_report_generation


class TriggerReportView(APIView):
    def post(self, request):
        # Trigger report generation here and return a report_id
        start_report_generation.send(sender=TriggerReportView, request=request)  # You can customize the signal

        return Response({'report_id': 'your_report_id'})


class GetReportView(APIView):
    def get(self, request, report_id):
        # Check the status of report generation
        # If it's complete, return the CSV file
        # If it's running, return "Running"
        return Response({'status': 'Complete', 'report_file': 'your_generated_report.csv'})
