"""Constants for the ePlate integration."""
from datetime import timedelta

tTime = "2023-3-1T6:57:00.000Z"  # basic_time only for test

DOMAIN ="ePlate"
#DOMAIN = "scheduletracker"
TIME_SHIFT = timedelta(hours=1)
BASE_API_URL = "https://spluseins.de/api/splus"

# types
LECT_TYPE = {0: "current", 1: "next"}
ROOM_TYPE = {0: "classroom type", 1: "office type"}
CMD_TYPE = {1: "refresh immediately", 2: "clear all", 3: "reset the display"}

# attributes
ATTR_ROOM_ID = "roomID"
ATTR_ROOM_TYPE = "roomType"
ATTR_QR = "roomQRCode"
ATTR_DIS = "roomDescribtion"
ATTR_DELAY = "delay"
ATTR_CMD = "command"
ATTR_DELAY_MIN = 1
ATTR_DELAY_MAX = 30
ATTR_SENSOR_MAX = 3
ATTR_MEMBER_MAX = 3
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
ATTR_SENSOR = "sensor"  # device_classes
ATTR_SENSOR_INFO = "sensor_info"
ATTR_SENSOR_UNIT = "sensor_unit"
ATTR_SENSOR_TYPE = "sensor_type"  # device_classes
# MQTT Discovery
DISCOVERY_TOPIC = "/ePlate/init/devices/#"
PATTERN_DISCOVERY = "/ePlate/init/devices/{unique_id}"
DISCOVERY_PAYLOAD = {
    "unique_id": "",
    "device": {
        "identifiers": "",
        "manufacturer": "",
        "model": "",
        "name": "",
        "sw_version": "",
    },
}
TOPIC_ID = ["init", "delay", "base", "room", "sensor"]
# topic-patterns
PATTERN_INIT = "/ePlate/{unique_id}/init/"
PATTERN_DELAY = "/ePlate/{roomID}/refreshTime"
PATTERN_BASE = "/ePlate/{roomID}/baseInfo"
PATTERN_CMD_FRESH = "/ePlate/{roomID}/refresh"
PATTERN_CMD_CLEAR = "/ePlate/{roomID}/clear"
PATTERN_CMD_RESET = "/ePlate/{roomID}/factoryReset"
PATTERN_CMD = [PATTERN_CMD_FRESH, PATTERN_CMD_CLEAR, PATTERN_CMD_RESET]
PATTERN_PLAN = "/ePlate/{roomID}/plannung"
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
PATTERN_BASE_PAYLOAD = {  # str
    ATTR_DIS: "",
    ATTR_QR: "",
}
PATTERN_PLAN_SUB_PAYLOAD = {
    ATTR_LECT: None,
    ATTR_INFO: None,
    ATTR_TIME: None,
}
PATTERN_PLAN_PAYLOAD = {
    LECT_TYPE[0]: PATTERN_PLAN_SUB_PAYLOAD,
    LECT_TYPE[1]: PATTERN_PLAN_SUB_PAYLOAD,
}
# i don like this:(
PLAN_PAYLOAD = {
    "classNow": None,
    "classNowRemainTime": None,
    "classNext": None,
    "classNextWaitTime": None,
    "classNextStartTime": None,
    "classNextEndTime": None,
}
# max 3 menbers
# PATTERN_MEMBER = {
#     ATTR_NAME: str,
#     ATTR_TEL: str,
#     ATTR_MAIL: str,
#     ATTR_MSG: str,
# }
PATTERN_MEMBER_PAYLOAD = {  # str
    "member1": {
        ATTR_NAME: "",
        ATTR_TEL: "",
        ATTR_MAIL: "",
        ATTR_MSG: "",
    },
    "member2": {
        ATTR_NAME: "",
        ATTR_TEL: "",
        ATTR_MAIL: "",
        ATTR_MSG: "",
    },
    "member3": {
        ATTR_NAME: "",
        ATTR_TEL: "",
        ATTR_MAIL: "",
        ATTR_MSG: "",
    },
}
# max 3 sensors
PATTERN_SENSOR_PAYLOAD = {
    ATTR_SENSOR: {
        ATTR_SENSOR_INFO: None,
        ATTR_SENSOR_UNIT: None,
        ATTR_SENSOR_TYPE: None,
    }
}
SENSOR_PAYLOAD = {
    ATTR_SENSOR: {
        ATTR_SENSOR_INFO: None,
        ATTR_SENSOR_UNIT: None,
        ATTR_SENSOR_TYPE: None,
    },
}
