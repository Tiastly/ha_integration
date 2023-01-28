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
    # get the current location information
    def __init__(self, location, timeInterval=5):
        self._lo = location
        self._now = None
        self._lect = {
            "title": 0,
            "start": None,
            "end": None,
            "duration": 0
        }
        self._nextLect = {
            "title": 0,
            "start": None,
            "end": None,
            "duration": 0
        }
        self._free = False
        self._updateTime = -1  # control restTime
        self._timeInter = timeInterval  # 5min restTime update interval

    def nowTime(self, now):
        """update at current time"""
        self._now = now

    @property
    def curr_lecture(self):
        """current lecture"""
        return self._lect["title"]

    @property
    def curr_lectInfo(self):
        """information about current lecture"""
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
        """information about next lecture"""
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

    def clear_next_lect(self):
        """clear current lecture"""
        self._nextLect = {
            "title": None,
            "start": None,
            "end": None,
            "duration": 0
        }

    @property
    def isFree(self):
        """classroom busy"""
        return self._free

    @isFree.setter
    def isFree(self, newState):
        """change free state"""
        self._free = newState

    @property
    def restTime(self):
        """rest time current lecture"""
        if self._lect["end"]:
            return self.timeFormat(self._lect["end"])

    @property
    def restTime_next(self):
        """rest time to next lecture"""
        if self._nextLect["start"]:
            return self.timeFormat(self._nextLect["start"])

    def updateTime(self):
        """force update lecture"""
        if self._updateTime - self._timeInter <= 0:
            if self.curr_lecture:
                self._updateTime = self.restTime
            elif self.next_lecture:
                self._updateTime = self.restTime_next
        else:
            self._updateTime -= self._timeInter
        return self._updateTime

    async def async_update(self, time):
        self.nowTime(time)
        # if any lecture has been scheduled
        # then not need to update the whole lecture, rather the rest of both time
        if self.curr_lecture is None and self.next_lecture is None:
            return  # now has no lecture LOCk
        if self._updateTime - self._timeInter <= 0:
            await self.async_update_lect()
        await self.async_update_rest()
        logger.info("free?{}\nlectInfo:{}\nrestTime:{}\nupDate:{}".format(
            self.isFree, [self.curr_lectInfo, self.next_lectInfo], [self.restTime, self.restTime_next], self._updateTime))

    async def async_update_rest(self):
        logger.info("Update restTime {}".format(self._now))
        self.updateTime()
        return [self.restTime, self.restTime_next]

    async def async_update_lect(self):
        # updateTime == 0, update the timetable, otherwise will only update restTime
        logger.info("Update from {}".format(self._now))
        location_plan = await Scrap(self._now, self._lo).lookup_location(self._lo)
        # if lecture["start"].date() == self._now.date():
        # today_lecture = []

        def positing(self, now: datetime) -> [dict, dict]:
            # 考虑删除表里内容 => 每天教室内容不多
            cur = None
            nex = None
            for i, lecture in enumerate(location_plan):
                lecture["start"] = self.timeConvert(lecture["start"])
                lecture["end"] = self.timeConvert(lecture["end"])
                if (self._now < lecture["end"]):  # has lecture
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
            self.clear_curr_lect()
            self.isFree = True
        # next has lesson
        if lecture[1]:
            self.next_lectInfo = lecture[1]
        # next dont have
        else:
            self.clear_next_lect()
        return [self.curr_lectInfo, self.next_lectInfo]

    # data processing help functions
    def timeConvert(self, time: str) -> datetime:
        """ change the starttime format only
        2022-12-19T09:00:00.000Z -> 2022-12-19 09:00:00+00.00
        """
        # return dt.strptime(time.replace('Z', '000'), '%Y-%m-%dT%H:%M:%S.%f')
        # python <=3.10
        return dateutil.parser.isoparse(time)
        # >3.10 dt.fromisoformat(time)

    def timeFormat(self, datetime):
        delta = abs(self._now - datetime)
        return round(delta.total_seconds()/60, 3)  # restTime in minute


if __name__ == "__main__":
    # dt.now(timezone.utc)
    t = "2022-12-21T10:20:00.000Z"
    basic_time = dateutil.parser.parse(t)
    interval = 15
    c = classroomData('A122', timeInterval=interval)
    loop = asyncio.get_event_loop()
    for step in range(0, interval*10, interval):
        now = basic_time + timedelta(minutes=step)
        future = asyncio.ensure_future(c.async_update(now))
    loop.run_until_complete(future)
