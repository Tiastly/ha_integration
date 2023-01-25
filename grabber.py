'''
semester based to room based
'''
import asyncio
import datetime
import aiohttp
import json
from timeit import default_timer
from concurrent.futures import ThreadPoolExecutor

studenplan = {
    'e_eit_gs_1_ws23',
    'e_eitip_gs_1_ws23',
    'e_weit_1_ws23',
    'e_weitip_1_ws23'
}

START_TIME = default_timer()


def weekInfo():
  today = datetime.date.today()
  number = today.isocalendar()[1]
  # isWeekend = today.isocalendar()[2]
  # return number
  return 52


async def single_request(url):
  data = []
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as request:
      try:
        assert request.status == 200
        resp = await request.json()
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

      except AssertionError:
        print("connection error")
      except Exception as e:
        print("expection in single_request:{}".format(e))
  print(data)
  return data

async def full_request():
  tasks = []
  week = weekInfo()
  for plan in studenplan:
    url = f'https://spluseins.de/api/splus/{plan}/{week}'
  await asyncio.gather(*task)
    # task = asyncio.ensure_future(single_request(url))
  # tasks = task.append()



async def start_async_process():
    print("{0:<30} {1:>20}".format("No", "Completed at"))
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            loop = asyncio.get_event_loop()
            START_TIME = default_timer()
            tasks = [
                loop.run_in_executor(
                    executor,
                    request,
                    *(session, i)
                )
                for i in range(15)
            ]
            for response in await asyncio.gather(*tasks):
                pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(single_request("https://spluseins.de/api/splus/e_eitip_gs_1_ws23/51"))
    loop.run_until_complete(future)
