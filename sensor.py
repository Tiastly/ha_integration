from scrap import Scrap


import datetime
from datetime import datetime as dt
from datetime import timedelta, date, timezone

import dateutil.parser
import asyncio
import logging
import sys


logging.basicConfig(
    format="%(asctime) s %(levelname) s:%(name) s: %(message) s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("sensor")
logging.getLogger("chardet.charsetprober") .disabled = True
class classroomData():
    # get the current location infomation
    def __init__(self, location, now):
        self._lo = location
        self._now = now
        self._lect = {
            "title": None,
            "start": None,
            "end": None,
            "duration": 0
        }
        self._nextLect = {
            "title": None,
            "start": None,
            "end": None,
            "duration": 0
        }
        self._free = False
        # control restTime
        self._updatetime = 0.5  # hours

    @property
    def curr_lecture(self):
        """current lecture"""
        return self._lect["title"]

    @property
    def curr_lectInfo(self):
        """infomation about current lecture"""
        return self._lect

    @curr_lectInfo.setter
    def curr_lectInfo(self, lecture: dict):
        """set current lecture"""
        self._lect = {
            "title": lecture["title"],
            "start": lecture["start"],
            "end": lecture["end"],
            "duration": lecture["duration"]
        }

    @curr_lectInfo.setter
    def clear_curr_lect(self):
        """clear current lecture"""
        self._lect = {
            "title": None,
            "start": None,
            "end": None,
            "duration": 0
        }

    @property
    def next_lecture(self):
        """next lecture"""
        return self._nextLect["title"]

    @property
    def next_lectInfo(self):
        """infomation about next lecture"""
        return self._nextLect

    @next_lectInfo.setter
    def next_lectInfo(self, lecture: dict):
        """set next lecture"""
        self._nextLect = {
            "title": lecture["title"],
            "start": lecture["start"],
            "end": lecture["end"],
            "duration": lecture["duration"]
        }

    @next_lectInfo.setter
    def clear_next_lect(self):
        """clear current lecture"""
        self._nextLect = {
            "title": None,
            "start": None,
            "end": None,
            "duration": 0
        }

    @property
    def restTime(self):
        """rest time current lecture"""
        return self.timeFormat(self._lectTime["end"])

    @property
    def restTime_next(self):
        """rest time to next lecture"""
        return self.timeFormat(self.__nextLectTime["start"])

    @property
    def isFree(self):
        """classroom busy"""
        return self._free

    @isFree.setter
    def isFree(self, newState):
        """change free state"""
        self._free = newState

    # @property
    # def updatetime(self):
    #     """updateTime"""
    #     return self._updatetime

    # data processing help functions
    def timeConvert(self, time: str) -> datetime:
        """ change the starttime format only
        2022-12-19T09:00:00.000Z -> 2022-12-19 09:00:00+00.00
        """
        # return dt.strptime(time.replace('Z', '000'), '%Y-%m-%dT%H:%M:%S.%f')
        # python <=3.10
        return dateutil.parser.isoparse(time)
        # >3.10 dt.fromisoformat(time)

    def timeFormat(self, datetime) -> str:
        delta = abs(self._now - datetime)
        if delta > timedelta(hours=1, minutes=30):
            return f'{datetime.hour}::{datetime.minute}'
        else:
            return delta.minute
    # todo

    async def async_update_rest(self):
        logger.info("Update restTime {}".format(self._now))
        return [self.restTime, self.toNextLecture]

    async def async_update(self):
        # updatetime == 0, update the timetable, otherwise will only update restTime
        logger.info("Update from {}".format(self._now))
        location_plan = await Scrap(self._now, self._lo).lookup_location(self._lo)
        # if lecture["start"].date() == self._now.date():
        # today_lecture = []

        def positing(self, now: datetime) -> [dict, dict]:
            # TODO linked list?
            # TODO 考虑删除表里内容
            cur = None
            nex = None
            for i, lecture in enumerate(location_plan):
                lecture["start"] = self.timeConvert(lecture["start"])
                lecture["end"] = self.timeConvert(lecture["end"])
                if (self._now <= lecture["end"]):  # has lecture
                    if (self._now >= lecture["start"]):
                        # find current
                        cur = lecture
                        try:
                            nex = location_plan[i+1]
                            nex["start"] = self.timeConvert(nex["start"])
                            nex["end"] = self.timeConvert(nex["end"])
                        except IndexError:
                            # current is the last
                            break
                    else:  # current is none
                        nex = location_plan[i]
                    break
            return [cur, nex]

        lecture = positing(self, self._now)
        # current has lesson
        if lecture[0]:
            self.curr_lectInfo = lecture[0]
            self.isFree = False
        else:  # current dont have
            self.clear_curr_lect(self)
            self.isFree = True
        # next has lesson
        if lecture[1]:
            self.next_lectInfo = lecture[1]
        # next dont have
        else:
            self.clear_next_lect()



if __name__ == "__main__":
    time = '2022-12-23T10:00:00.000Z'
    now = dateutil.parser.parse(time)
    # dt.now(timezone.utc)
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(classroomData('Online', now).async_update())
    loop.run_until_complete(future)
