import pytz
from datetime import datetime
from django.core.cache import cache
import csv
from django.db.models import Avg
from django.db.models.functions import TruncHour
from datetime import datetime, timedelta
from django.utils import timezone
from .models import StoreActivity, StoreBusinessHours, StoreTimezone


def generate_report():
    # Get the current timestamp
    current_time = datetime.now()

    # Define the file path and name for the CSV report
    report_file_path = '/path/to/your/report/folder/report.csv'

    # Create a CSV writer
    with open(report_file_path, 'w', newline='') as report_file:
        writer = csv.writer(report_file)

        # Write the header row
        writer.writerow([
            'store_id',
            'uptime_last_hour (minutes)',
            'uptime_last_day (hours)',
            'uptime_last_week (hours)',
            'downtime_last_hour (minutes)',
            'downtime_last_day (hours)',
            'downtime_last_week (hours)'
        ])

        # Get all store IDs
        store_ids = StoreActivity.objects.values_list('store_id', flat=True).distinct()

        for store_id in store_ids:
            # Get the store's business hours
            business_hours = StoreBusinessHours.objects.filter(store_id=store_id)

            # Get the store's timezone
            timezone_info = StoreTimezone.objects.filter(store_id=store_id).first()
            timezone_str = 'America/Chicago'  # Default timezone
            if timezone_info:
                timezone_str = timezone_info.timezone_str

            # Calculate time intervals
            last_hour_start = current_time - timedelta(hours=1)
            last_day_start = current_time - timedelta(days=1)
            last_week_start = current_time - timedelta(weeks=1)

            # Convert timestamps to the store's local timezone
            last_hour_start_local = last_hour_start.astimezone(timezone(timezone_str))
            last_day_start_local = last_day_start.astimezone(timezone(timezone_str))
            last_week_start_local = last_week_start.astimezone(timezone(timezone_str))

            # Calculate uptime and downtime
            uptime_last_hour = calculate_uptime(store_id, last_hour_start, current_time, business_hours)
            uptime_last_day = calculate_uptime(store_id, last_day_start, current_time, business_hours)
            uptime_last_week = calculate_uptime(store_id, last_week_start, current_time, business_hours)

            downtime_last_hour = (last_hour_start - uptime_last_hour).total_seconds() / 60
            downtime_last_day = (last_day_start - uptime_last_day).total_seconds() / 3600
            downtime_last_week = (last_week_start - uptime_last_week).total_seconds() / 3600

            # Write the data to the CSV
            writer.writerow([
                store_id,
                uptime_last_hour.total_seconds() / 60,
                uptime_last_day.total_seconds() / 3600,
                uptime_last_week.total_seconds() / 3600,
                downtime_last_hour,
                downtime_last_day,
                downtime_last_week,
            ])

    return report_file_path


def calculate_uptime(store_id, start_time, end_time, business_hours):
    # Calculate uptime within business hours
    uptime = StoreActivity.objects.filter(
        store_id=store_id,
        timestamp_utc__gte=start_time,
        timestamp_utc__lte=end_time,
        status='active'
    )

    # Group by hour and get the average uptime
    uptime = uptime.annotate(hour=TruncHour('timestamp_utc')).values('hour').annotate(
        avg_uptime=Avg('status')
    )

    return uptime


def cache_fun():
    # Set the shared variable
    cache.set('shared_variable', 'initial_value')

    # Retrieve the shared variable
    value = cache.get('shared_variable')

    # Update the shared variable
    cache.set('shared_variable', 'new_value')


def change_string_to_time():
    pass


def check_if_open_hour():
    # Assuming you have a store's UTC timestamp and their timezone string
    utc_timestamp = datetime(2023, 10, 31, 12, 0, 0, tzinfo=pytz.utc)
    local_timezone = pytz.timezone('America/Chicago')

    # Convert UTC timestamp to local time
    local_time = utc_timestamp.astimezone(local_timezone)

    # Check if the local time falls within business hours (you might need to iterate through days of the week)
    business_start_time = local_time.replace(hour=9, minute=0, second=0, microsecond=0)
    business_end_time = local_time.replace(hour=17, minute=0, second=0, microsecond=0)

    # converting string to pytz object format
    # Sample string
    date_string = "2023-01-22 12:09:39.388884 UTC"

    # Define the format of the input string
    date_format = "%Y-%m-%d %H:%M:%S.%f %Z"

    # Convert the string to a datetime object in the desired timezone (UTC)
    date_obj = datetime.strptime(date_string, date_format).astimezone(pytz.UTC)

    if business_start_time <= local_time <= business_end_time:
        print("Store is open during local business hours.")
    else:
        print("Store is closed during local business hours.")


def group_and_sort_times_by_date(datetime_strings):
    # Create a dictionary to store times by date
    times_by_date = {}

    for dt_string in datetime_strings:
        # Parse the datetime string
        dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S %Z')

        # Extract the date part as a string
        date_str = dt.strftime('%Y-%m-%d')

        # Add the time to the list for the corresponding date
        if date_str in times_by_date:
            times_by_date[date_str].append(dt.strftime('%H:%M:%S'))
        else:
            times_by_date[date_str] = [dt.strftime('%H:%M:%S')]

    # Sort the times for each date
    for date, times in times_by_date.items():
        times_by_date[date] = sorted(times)

    return times_by_date
