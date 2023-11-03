from asgiref.sync import sync_to_async
from .utils import generate_report
from django.core.cache import cache


@sync_to_async
def start_report_generation_handler(report_id):

    generate_report(report_id=report_id)

    cache.set(report_id, True)

    return "Task completed"
