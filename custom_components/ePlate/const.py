"""Constants for the ePlate integration."""
from datetime import timedelta

t = "2022-12-22T6:57:00.000Z"  # basic_time only for test

DOMAIN ="ePlate"
TIME_SHIFT = timedelta(hours=1)
BASE_API_URL = "https://spluseins.de/api/splus"

# types
LECT_TYPE = {0: "current", 1: "next"}
ROOM_TYPE = {0: "classroom type", 1: "office type"}


# attributes
ATTR_ROOM_ID = "room_id"
ATTR_ROOM_TYPE = "room_type"
ATTR_QR = "room_qr-code"
ATTR_DIS = "room_description"
ATTR_DELAY = "delay"
ATTR_DELAY_MIN = 1
ATTR_DELAY_MAX = 30
ATTR_SENSOR_MAX = 3
# class
ATTR_LECT = "lectures"
ATTR_INFO = "lect_info"
ATTR_TIME = "rest/begin_time"
# office
ATTR_NAME = "name"
ATTR_TEL = "tel"
ATTR_MAIL = "email"
ATTR_MSG = "describtion"  # describtion msg
# sensor
ATTR_SENSOR = "sensor"
ATTR_SENSOR_INFO = "sensor_info"
# MQTT Discovery
DISCOVERY_TOPIC = "/ePlate/init/devices/#"
PATTERN_DISCOVERY = "/ePlate/init/devices/{unique_id}"
DISCOVERY_PAYLOAD ={
 "unique_id": "",
 "device": {
     "identifiers": "",
     "manufacturer": "",
     "model": "",
     "name": "",
     "sw_version": "" }
}
TOPIC_ID = ["init", "delay", "base", "room", "sensor"]
# topic-patterns
PATTERN_INIT = "/ePlate/{unique_id}/init/"
PATTERN_DELAY = "/ePlate/{roomID}/refreshTime"
PATTERN_BASE = "/ePlate/{roomID}/baseInfo"
PATTERN_PLAN = "/ePlate/{roomID}/planung"
PATTERN_MEMBER = "/ePlate/{roomID}/member"
PATTERN_SENSOR = "/ePlate/{roomID}/sensor"
# payload-patterns
PATTERN_INIT_PAYLOAD = {  # from init
    ATTR_ROOM_ID: str,
    ATTR_ROOM_TYPE: ROOM_TYPE,
    ATTR_DELAY: int,
}
# only numbers
PATTERN_DELAY_PAYLOAD = {
    ATTR_DELAY: int,
}
PATTERN_BASE_PAYLOAD = {
    ATTR_DIS: str,
    ATTR_QR: str,
    # ATTR_DELAY: str,
}
PATTERN_PLAN_SUB_PAYLOAD = {
    ATTR_LECT: str,
    ATTR_INFO: str,
    ATTR_TIME: str,
}
PATTERN_PLAN_PAYLOAD = {
    LECT_TYPE[0]: PATTERN_PLAN_SUB_PAYLOAD ,
    LECT_TYPE[1]: PATTERN_PLAN_SUB_PAYLOAD ,
}
# i don like this:(
PLAN_PAYLOAD = {
    "classNow": str,
    "classNowRemainTime": int,
    "classNext": str,
    "classNextWaitTime": int,
    "classNextStartTime": str,
    "classNextEndTime": str,
}
# max 3 menbers
# PATTERN_MEMBER = {
#     ATTR_NAME: str,
#     ATTR_TEL: str,
#     ATTR_MAIL: str,
#     ATTR_MSG: str,
# }
PATTERN_MEMBER_PAYLOAD = {
    "member1": {
        ATTR_NAME: str,
        ATTR_TEL: str,
        ATTR_MAIL: str,
        ATTR_MSG: str,
    },
    "member2": {
        ATTR_NAME: str,
        ATTR_TEL: str,
        ATTR_MAIL: str,
        ATTR_MSG: str,
    },
    "member3": {
        ATTR_NAME: str,
        ATTR_TEL: str,
        ATTR_MAIL: str,
        ATTR_MSG: str,
    },
}
# max 3 sensors
PATTERN_SENSOR_PAYLOAD = {ATTR_SENSOR: ATTR_SENSOR_INFO}
SENSOR_PAYLOAD = {
    "sensor1": {
        ATTR_SENSOR: str,
        ATTR_SENSOR_INFO: str,
    },
    "sensor2": {
        ATTR_SENSOR: str,
        ATTR_SENSOR_INFO: str,
    },
    "sensor3": {
        ATTR_SENSOR: str,
        ATTR_SENSOR_INFO: str,
    },
}
