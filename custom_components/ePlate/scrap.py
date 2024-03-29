"""api scrap and row processing."""
from __future__ import annotations

import concurrent.futures
from datetime import datetime, timedelta
import pytz
import json
import logging

import aiofiles
import aiohttp
import dateutil.parser

from .const import BASE_API_URL, TIME_ZONE
from .studenplan import STUDEN_PLAN

_logger = logging.getLogger(__name__)


#  today's all timetable
class Scrap:
    """scrap the classinfomation."""

    def __init__(self, session, time) -> None:
        self._now = time
        self._session = session

    def week_info(self):
        """week infomation."""
        today = self._now.date()
        number = today.isocalendar()[1]
        return number

    async def single_request(self, url: str):
        """processing the single url requst."""
        data = []
        try:
            async with self._session.get(url, timeout=30) as response:
                response.raise_for_status()
                _logger.debug("Got response [%s] for URL: %s", response.status, url)
                resp = await response.json()
                resp = resp["events"]
                if resp:
                    _logger.debug("Found lecture")
                    for lecture in resp:
                        # only scrap todays lectures
                        if lecture["start"][:10] == (self._now.date()).isoformat():
                            if "id" and "meta" and "duration" in lecture:
                                lecture.pop("id")
                                lecture.pop("duration")
                                lecture.pop("meta")
                            data.append(lecture)
        except (
            aiohttp.ClientError,
            aiohttp.http_exceptions.HttpProcessingError,
        ) as aio_exceptions:
            _logger.debug(
                "aiohttp exception for %s [%s]: %s",
                url,
                getattr(aio_exceptions, "status", None),
                getattr(aio_exceptions, "message", None),
            )
        except Exception as other_exceptions:  # pylint: disable=broad-except
            _logger.exception("Non-aiohttp exception %s occured", other_exceptions)

        return data

    async def full_request(self):
        """processing todays all classroom infomation."""
        tasks = []
        week = self.week_info()
        urls = []
        for plan in STUDEN_PLAN:
            urls.append(f"{BASE_API_URL}/{plan}/{week}")
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(STUDEN_PLAN)
        ) as executor:
            future_to_url = [executor.submit(self.single_request, url) for url in urls]
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    tasks += await future.result()
                except Exception as exceptions:  # pylint: disable=broad-except
                    _logger.debug("exception %s at full_request occured", exceptions)

        return [dict(t) for t in {tuple(d.items()) for d in tasks}]

    async def reorder_as_location(self):
        """reorder the infomation to classroom order."""
        from copy import deepcopy

        room = []
        semester = await self.full_request()
        for lecture in semester:
            for lo in lecture["location"].split(","):
                dummy_lec = deepcopy(lecture)
                # HS A, P6, P7 has space after comma
                dummy_lec["location"] = lo.lstrip()[:4]
                room.append(dummy_lec)
        return sorted(room, key=lambda tasks: (tasks["location"], tasks["start"]))

    async def write_local(self, file):
        """save the timetable."""
        res = await self.reorder_as_location()
        async with aiofiles.open(file, "w+") as f:
            await f.write(json.dumps(res, indent=4))
            await f.flush()
        _logger.debug("Wrote results in %s", self._now.date())

    async def lookup_location(self, location=None):
        """default update all."""
        import os

        paths = f"{os.path.abspath(os.curdir)}/custom_components/ePlate/room"
        if not os.path.exists(paths):
            os.makedirs(paths)
        files = f"{paths}/roomplan_{self._now.date()}.json"
        if not os.path.isfile(files):
            await self.write_local(file=files)
        try:
            with open(files, encoding="utf-8") as f:
                room = json.loads(f.read())
            if not location:
                _logger.debug("Daily update at %s", self._now.date())
                return room
            res = []

            for lecture in room:
                if lecture["location"] == location:
                    res.append(lecture)
                elif res:
                    _logger.debug("lookup location %s at %s", location, self._now.date())
                    return res
            _logger.debug(
                "%s infos at location %s in %s find", len(res), location, self._now.date()
            )
            return res

        except json.decoder.JSONDecodeError:  # today has no lecture
            _logger.debug("%s has no lecture", self._now.date())
            return []
        except OSError as io_error:
            _logger.debug("I/O error %s): %s", io_error.errno, io_error.strerror)
        except Exception as exceptions:  # pylint: disable=broad-except
            _logger.debug("Unexpected error %s", exceptions)


class ClassroomData:
    """each classroom has one dataclass,
    get the current location information.
    """

    def __init__(self, session, location, time_interval) -> None:
        self._location = location
        self._now = None
        self._session = session
        self._lect = {
            "title": 0,
            "start": None,
            "end": None,
        }
        self._next_lect = {
            "title": 0,
            "start": None,
            "end": None,
        }
        self._free = False
        self._update_time = -1  # see async_update_lect
        self._time_interval = time_interval  # only refresh/update rest_time

    @property
    def now(self):
        """update current time."""
        self._now = datetime.now(tz=TIME_ZONE)
        return self._now

    @property
    def locations(self):
        """roomName."""
        return self._lo

    @property
    def curr_lecture(self):
        """current lecture."""
        return self._lect["title"]

    @property
    def curr_info(self):
        """information about current lecture."""
        return (
            {
                "start": self._lect["start"].strftime("%H:%M"),
                "end": self._lect["end"].strftime("%H:%M"),
            }
            if self.curr_lecture
            else None
        )

    @curr_info.setter
    def curr_info(self, lecture: dict):
        """set current lecture."""
        self._lect = {
            "title": lecture["title"],
            "start": lecture["start"],
            "end": lecture["end"],
        }

    def _clear_curr_lect(self):
        """clear current lecture."""
        self._lect = {
            "title": None,
            "start": None,
            "end": None,
        }

    @property
    def next_lecture(self):
        """next lecture."""
        return self._next_lect["title"]

    @property
    def next_info(self):
        """information about next lecture."""
        return (
            {
                "start": self._next_lect["start"].strftime("%H:%M"),
                "end": self._next_lect["end"].strftime("%H:%M"),
            }
            if self.next_lecture
            else None
        )

    @next_info.setter
    def next_info(self, lecture: dict):
        """set next lecture."""
        self._next_lect = {
            "title": lecture["title"],
            "start": lecture["start"],
            "end": lecture["end"],
        }

    def _clear_next_lect(self):
        """clear current lecture."""
        self._next_lect = {
            "title": None,
            "start": None,
            "end": None,
        }

    @property
    def is_free(self):
        """classroom busy."""
        return self._free

    @property
    def rest_time(self):
        """rest time current lecture."""
        if self._lect["end"]:
            return self._time_format(self._lect["end"])

    @property
    def begin_time(self):
        """rest time to next lecture."""
        if self._next_lect["start"]:
            return self._time_format(self._next_lect["start"])

    def update_time(self):
        """force update lecture."""
        if self._update_time - self._time_interval <= 0:
            if self.curr_lecture:
                self._update_time = self.rest_time
            elif self.next_lecture:
                self._update_time = self.begin_time
        else:
            self._update_time -= self._time_interval
        return self._update_time

    async def async_update(self):
        """update the infomation in time_interval."""
        _logger.debug(
            "now:%s,curr:%s,next%s", self._now, self.curr_lecture, self._next_lect
        )
        # time here means current time
        # if any lecture has been scheduled
        # then not need to update the whole lecture, rather the rest of both time
        if self.curr_lecture is None and self.next_lecture is None:
            return  # now has no lecture LOCk
        if self._update_time - self._time_interval <= 0:
            await self.async_update_lect()
        await self.async_update_rest()

    async def async_update_rest(self):
        """only update the rest_time and begin_time."""
        _logger.debug("Update from rest%s", self._now)
        self.update_time()
        return [self.rest_time, self.begin_time]

    async def async_update_lect(self):
        """update the lecture infomation."""
        # update_time == 0, update the timetable/lect, otherwise will only update rest_time
        _logger.debug("Update from lect%s,location %s", self._now, self._location)

        location_plan = await Scrap(
            session=self._session, time=self._now
        ).lookup_location(self._location)

        def positing():
            nex = cur = None
            for i, lecture in enumerate(location_plan):
                lecture["start"] = self._time_convert(lecture["start"])
                lecture["end"] = self._time_convert(lecture["end"])
                if self._now.timestamp() < lecture["end"].timestamp():  # has lecture
                    _logger.debug("i find %s", lecture["end"])
                    if self._now.timestamp() >= lecture["start"].timestamp():
                        # find current
                        cur = lecture
                        _logger.debug("cur is:%s", cur)
                        try:
                            nex = location_plan[i + 1]
                            nex["start"] = self._time_convert(nex["start"])
                            nex["end"] = self._time_convert(nex["end"])

                        except IndexError:
                            # current is the last
                            break
                    else:  # current is none
                        nex = location_plan[i]
                    break
                _logger.debug("cur:%s,next:%s", cur, nex)
            return [cur, nex]

        cur, nex = positing()
        # current has lesson
        if cur:
            self.curr_info = cur
            self._free = False
        else:  # current dont have
            self._clear_curr_lect()
            self._free = True
        # next has lesson
        if nex:
            self.next_info = nex
        # next dont have
        else:
            self._clear_next_lect()
        return [self.curr_info, self.next_info]

    # data processing help functions
    def _time_convert(self, time: str) -> datetime:
        """change the starttime format only."""
        return (
            dateutil.parser.isoparse(time)
            .replace(tzinfo=pytz.UTC)
            .astimezone(TIME_ZONE)
        )

    def _time_format(self, date_time):
        """ "change the time format to minutes"""
        return round(
            abs(date_time - self._now).total_seconds() / 60, 3
        )  # rest_time in minute
