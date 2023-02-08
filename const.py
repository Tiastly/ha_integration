"""Constants for the scheduletracker integration."""
from datetime import timedelta
from enum import Enum
DOMAIN = "scheduletracker"
TIME_SHIFT = timedelta(hours=1)
t = "2022-12-22T6:57:00.000Z"  # basic_time only for test
CONF_DEFAULT_NOTIFICATION_TITLE = "CONF_DEFAULT_NOTIFICATION_TITLE"
BASE_API_URL = "https://spluseins.de/api/splus"
CONF_CONTROLLER = "test"

class LectureType(Enum):
    """lecture types"""
    CURRENT = "current_lecture",
    NEXT = "next_lecture"

SCAN_INTERVAL= timedelta(minutes=1)
ATTR_LECT = "lectures"
ATTR_INFO = "lect_info"
ATTR_TIME = "rest/begin_time"