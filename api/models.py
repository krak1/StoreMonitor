from django.db import models


class StoreTimezone(models.Model):
    store_id = models.CharField(max_length=30)
    timezone = models.CharField(max_length=32)


class StoreBusinessHours(models.Model):
    store_id = models.CharField(max_length=30)
    day_of_week = models.PositiveSmallIntegerField()
    start_time_local = models.CharField(max_length=16)
    end_time_local = models.CharField(max_length=16)


class StoreActivity(models.Model):
    store_id = models.CharField(max_length=30)
    timestamp_utc = models.CharField(max_length=32)
    status = models.CharField(max_length=8)  # 'active' or 'inactive'
