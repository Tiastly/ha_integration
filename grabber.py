'''
semester based to room based
'''
import asyncio
import aiohttp
import concurrent.futures
# from concurrent.futures import ThreadPoolExecutor
import datetime
import json
import logging
import sys
import aiofiles


studenplan = {
    'e_eit_gs_1_ws23',
    'e_eitip_gs_1_ws23',
    'e_weit_1_ws23',
    'e_weitip_1_ws23',
    # "e_eit_ip_gs_2_ws23",
    # "e_weit_ip_2_ws23",
    # "e_eit_ip_gs_neu_3_ws23",
    # "e_eit_ip_gs_alt_3_ws23",
    # "e_weit_ip_neu_3_ws23",
    # "e_weit_ip_alt_3_ws23",
}

logging.basicConfig(
    format="%(asctime) s %(levelname) s:%(name) s: %(message) s",
    level=logging.DEBUG,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("grabber")
logging.getLogger("chardet.charsetprober") .disabled = True



def weekInfo():
    today = datetime.date.today()
    number = today.isocalendar()[1]
    # isWeekend = today.isocalendar()[2]
    # return number
    return 51


async def single_request(url: str, **kwargs):
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
            "Non-aiohttp exception occured:  %s", getattr(e, "__dict__", {})
        )
    logger.info("Found lecture") if resp else logger.info("not Found lecture")
    return data


async def full_request():
    tasks = []
    week = weekInfo()
    urls = []
    for plan in studenplan:
        urls.append(f'https://spluseins.de/api/splus/{plan}/{week}')
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(studenplan)) as executor:
        future_to_url = [executor.submit(single_request, url) for url in urls]
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


async def reorder_as_location():
    from copy import deepcopy
    classroom = []
    semester = await full_request()
    for lecture in semester:
        for lo in lecture["location"].split(','):
            dummy_lec = deepcopy(lecture)
            #HS A, P6, P7 has space after comma
            dummy_lec["location"] = lo.lstrip()
            classroom.append(dummy_lec)
    return sorted(classroom, key=lambda tasks: (tasks['location'], tasks['start']))


async def write_local(file):
    res = await reorder_as_location()
    async with aiofiles.open(file, "w+") as f:
        await f.write(json.dumps(res, indent=4))
        await f.flush()
    logger.info("Wrote results in %s", datetime.date.today())


async def lookup_location(lo=None):
    '''
    default update all
    '''
    import os
    files = f"room\\roomplan_{datetime.date.today()}.json"
    if not os.path.isfile(files):
        await write_local(file=files)

    try:
        with open(files, "r") as f:
            classroom = json.loads(f.read()) 
        if not lo:
            logger.info("Daily update at %s", datetime.date.today())
            return classroom
        res = []
        for lecture in classroom:
            if lecture["location"] == lo:
                res.append(lecture)
            if lecture["location"] != lo and res:
                logger.info("lookup location %s at %s",
                            lo, datetime.date.today())
                print(len(res))
                return res
        logger.info("no location %s at %s find", lo, datetime.date.today())
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
    loop = asyncio.get_event_loop()
    #trouble with online P1 P7
    future = asyncio.ensure_future(lookup_location('Online'))
    loop.run_until_complete(future)
