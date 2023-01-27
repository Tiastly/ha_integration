'''
semester based to room based
'''
import asyncio
import aiohttp
import concurrent.futures
# from concurrent.futures import ThreadPoolExecutor
import datetime
from datetime import date


import json
import logging
import sys
import aiofiles

from studenplan import STUDEN_PLAN

logging.basicConfig(
    format="%(asctime) s %(levelname) s:%(name) s: %(message) s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("scrap")
logging.getLogger("chardet.charsetprober") .disabled = True


class Scrap():
    def __init__(self, now, location = None):
        self._now = now
        self._lo = location

    def weekInfo(self):
        today = self._now.date()
        number = today.isocalendar()[1]
        # isWeekend = today.isocalendar()[2]
        # return number
        return 51

    # 只要当天的课表就行

    async def single_request(self, url: str, **kwargs):
        data = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    logger.info(
                        "Got response [%s] for URL: %s", response.status, url)
                    resp = await response.json()
                    resp = resp["events"]
                    if resp:
                        for lecture in resp:
                            # only scrap todays lectures
                            if lecture["start"][:10] == self._now.date().isoformat():
                                if "id" and "meta" in lecture:
                                    lecture.pop("id")
                                    lecture.pop("meta")
                            # data["title"] = lecture["title"]
                            # data["start"] = lecture["start"]
                            # data["end"] = lecture["end"]
                            # data["duration"] = lecture["duration"]
                            # data["location"] = lecture["location"]
                                data.append(lecture)
        except (
            aiohttp.ClientError,
            aiohttp.http_exceptions.HttpProcessingError,
        ) as e:
            logger.error(
                "aiohttp exception for %s [%s]: %s",
                url,
                getattr(e, "status", None),
                getattr(e, "message", None),
            )
        except Exception as e:
            # May be raised from other libraries, such as chardet or yarl.
            # logger.exception will show the full traceback.
            logger.exception(
                "Non-aiohttp exception occured:  %s", getattr(
                    e, "__dict__", {})
            )
        logger.info("Found lecture") if resp else logger.info(
            "not Found lecture")
        return data

    async def full_request(self):
        tasks = []
        week = self.weekInfo()
        urls = []
        for plan in STUDEN_PLAN:
            urls.append(f'https://spluseins.de/api/splus/{plan}/{week}')
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(STUDEN_PLAN)) as executor:
            future_to_url = [executor.submit(
                self.single_request, url) for url in urls]
            for future in concurrent.futures.as_completed(future_to_url):
                try:
                    tasks += await future.result()
                except Exception as e:
                    logger.exception(
                        "exception at full_request occured:  %s", getattr(
                            e, "__dict__", {})
                    )

        # for url in urls:
        #     task += single_request(url)
        # tasks = await asyncio.gather(*task)

        return [dict(t) for t in {tuple(d.items()) for d in tasks}]

    async def reorder_as_location(self,):
        from copy import deepcopy
        classroom = []
        semester = await self.full_request()
        for lecture in semester:
            for lo in lecture["location"].split(','):
                dummy_lec = deepcopy(lecture)
                # HS A, P6, P7 has space after comma
                dummy_lec["location"] = lo.lstrip()
                classroom.append(dummy_lec)
        return sorted(classroom, key=lambda tasks: (tasks['location'], tasks['start']))

    async def write_local(self, file):
        res = await self.reorder_as_location()
        async with aiofiles.open(file, "w+") as f:
            await f.write(json.dumps(res, indent=4))
            await f.flush()
        logger.info("Wrote results in %s", self._now.date())

    async def lookup_location(self, lo):
        '''
        default update all
        '''
        import os
        files = f"room/roomplan_{self._now.date()}.json"
        if not os.path.isfile(files):
            await self.write_local(file=files)

        try:
            with open(files, "r") as f:
                classroom = json.loads(f.read())
            if not lo:
                logger.info("Daily update at %s", self._now.date())
                return classroom
            res = []
            for lecture in classroom:
                if lecture["location"] == lo:
                    res.append(lecture)
                elif res:
                    # if lecture["location"] != lo and res:
                    logger.info("lookup location %s at %s",
                                lo, self._now.date())
                    return res
            logger.info("{0} infos at location {1} in {2} find".format(
                        len(res),lo, self._now.date()))
            return res

        except IOError as e:
            logger.exception(
                "I/O error({0}): {1}".format(e.errno, e.strerror)
            )
        except Exception as e:
            logger.exception(
                "Unexpected error opening {fname} is", getattr(
                    e, "__dict__", {})
            )


if __name__ == "__main__":
    import dateutil.parser
    time = '2022-12-23T10:00:00.000Z'
    now = dateutil.parser.parse(time)
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(Scrap(now).lookup_location("Online"))
    loop.run_until_complete(future)
