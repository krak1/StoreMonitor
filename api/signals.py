from django.dispatch import Signal, receiver

start_report_generation = Signal()


def start_report_generation_handler(sender, **kwargs):
    # Your signal handler logic
    return "Signal called!"
