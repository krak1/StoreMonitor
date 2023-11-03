import csv
import pytz
from datetime import datetime
from django.db.models import Avg, Case, When, Value, IntegerField, DateTimeField
from django.db.models.functions import TruncHour, Cast
from django.core.cache import cache

from .models import StoreActivity, StoreBusinessHours, StoreTimezone


def generate_report(report_id):
    # Defining timestamps according to the datasets.
    current_time = change_string_to_time("2023-01-25 18:13:22.47922 UTC")
    last_hour_start = change_string_to_time("2023-01-25 17:13:22.47922 UTC")
    last_day_start = change_string_to_time("2023-01-24 18:13:22.47922 UTC")
    last_week_start = change_string_to_time("2023-01-18 00:00:03.24375 UTC")

    # Define the file path and name for the CSV report
    report_file_path = 'api/report/' + report_id + '.csv'

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
        store_ids_size = len(store_ids)

        for i, store_id in enumerate(store_ids):
            # Get the store's timezone
            timezone_info = StoreTimezone.objects.filter(store_id=store_id).first()
            timezone_str = 'America/Chicago'  # Default timezone
            if timezone_info:
                timezone_str = timezone_info.timezone

            # Calculate uptime and downtime
            uptime_queryset = return_calculate_uptime_queryset(store_id, last_week_start, current_time, timezone_str)

            uptime_last_hour, downtime_last_hour = count_uptime_downtime_hours(uptime_queryset, last_hour_start,
                                                                               current_time)
            uptime_last_day, downtime_last_day = count_uptime_downtime_hours(uptime_queryset, last_day_start,
                                                                             current_time)
            uptime_last_week, downtime_last_week = count_uptime_downtime_hours(uptime_queryset, last_week_start,
                                                                               current_time)

            # Write the data to the CSV
            writer.writerow([
                store_id,
                uptime_last_hour / 60,
                uptime_last_day,
                uptime_last_week,
                downtime_last_hour / 60,
                downtime_last_day,
                downtime_last_week,
            ])

            cache.set("items_done", str(i)+"/"+str(store_ids_size))

            if i == 10:
                break

    print("--> file saved!")
    return report_file_path


def return_calculate_uptime_queryset(store_id, start_time, end_time, store_timezone):
    # Retrieve all timestamp_utc values for the store within the specified time range
    timestamps = StoreActivity.objects.filter(
        store_id=store_id,
        # timestamp_utc__gte=start_time,
        # timestamp_utc__lte=end_time
    ).values('id', 'timestamp_utc', 'status')

    # Filter timestamps within the specified time range
    filtered_data = []
    for ts in timestamps:
        ts_time = pytz.UTC.localize(ts['timestamp_utc'])
        if (start_time <= ts_time <= end_time and
                is_within_business_hours(store_id, ts['timestamp_utc'], store_timezone)):
            filtered_data.append(ts)

    return get_active_hours_for_each_timestamp(filtered_data)


def count_uptime_downtime_hours(uptime_queryset, start_time, end_time):
    uptime, downtime = 0, 0
    for item in uptime_queryset:
        if start_time <= item['hour'] <= end_time:
            uptime += item['avg_uptime']
            downtime += 1 - item['avg_uptime']

    return uptime, downtime


def get_active_hours_for_each_timestamp(list_data):
    # Convert the list into a QuerySet
    queryset = StoreActivity.objects.filter(id__in=[item['id'] for item in list_data])

    # Apply the aggregation operations
    result = (
        queryset
        .annotate(
            timestamp_utc_datetime=Cast('timestamp_utc', output_field=DateTimeField())
        )
        .annotate(hour=TruncHour('timestamp_utc_datetime'))
        .values('hour')
        .annotate(
            avg_uptime=Avg(
                Case(
                    When(status='active', then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            )
        )
    )

    return result


def change_string_to_time(str_time):
    datetime_format = "%Y-%m-%d %H:%M:%S.%f %Z"
    return datetime.strptime(str_time, datetime_format).astimezone(pytz.UTC)


def is_within_business_hours(store_id, timestamp, store_timezone):
    # converting utc time to local time
    local_timezone = pytz.timezone(store_timezone)
    local_time = timestamp.astimezone(local_timezone)

    # Get the store's business hours
    day_of_week = timestamp.weekday() - 1
    business_hours = StoreBusinessHours.objects.filter(store_id=store_id, day_of_week=day_of_week)

    if len(business_hours) > 0:
        business_start_time = add_date_to_time(business_hours[0].start_time_local,
                                               local_time,
                                               local_timezone)
        business_end_time = add_date_to_time(business_hours[0].end_time_local,
                                             local_time,
                                             local_timezone)
    else:
        # open 24*7
        business_start_time = datetime.min.replace(tzinfo=pytz.UTC)
        business_end_time = datetime.max.replace(tzinfo=pytz.UTC)

    if business_start_time <= local_time <= business_end_time:
        return True
    else:
        return False


def add_date_to_time(time_str, another_timestamp, timezone):
    combined_datetime = another_timestamp.replace(
        hour=int(time_str.split(':')[0]),
        minute=int(time_str.split(':')[1]),
        second=int(time_str.split(':')[2])
    )

    return combined_datetime
