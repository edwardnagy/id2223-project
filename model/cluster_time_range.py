from datetime import date, timedelta
from enum import Enum


class ClusterTimeRange(Enum):
    LAST_MONTH = 1
    LAST_HALF_YEAR = 2
    LAST_YEAR = 3

    def get_start_date(self) -> date:
        """Get the start date for the provided time range."""

        today = date.today()

        # Get the first day of the previous month
        if today.month == 1:
            first_day_of_previous_month = today.replace(
                year=today.year - 1, month=12, day=1
            )
        else:
            first_day_of_previous_month = today.replace(month=today.month - 1, day=1)

        # Get the start date for the provided time range
        if self == ClusterTimeRange.LAST_MONTH:
            start_date = first_day_of_previous_month
        elif self == ClusterTimeRange.LAST_HALF_YEAR:
            if today.month <= 6:
                month = 12 - (6 - today.month)
                start_date = today.replace(year=today.year - 1, month=month, day=1)
            else:
                start_date = today.replace(month=today.month - 6, day=1)
        elif self == ClusterTimeRange.LAST_YEAR:
            start_date = today.replace(year=today.year - 1, day=1)

        return start_date

    def get_end_date(self) -> date:
        """Get the end date for the provided time range."""

        today = date.today()
        end_date = today.replace(day=1) - timedelta(days=1)

        return end_date
