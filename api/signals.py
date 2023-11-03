from django.dispatch import Signal
from .utils import generate_report
from django.core.cache import cache

start_report_generation = Signal()


def start_report_generation_handler(sender, report_id, **kwargs):
    print("293-Signal Invoked!")
    generate_report(report_id=report_id)

    cache.set(report_id, True)

    return "Signal completed"
