'''
semester based to room based
'''
import asyncio
import datetime
import requests
import json

# from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

studenplan = {
    'e_eit_gs_1_ws23',
    'e_eitip_gs_1_ws23',
    'e_weit_1_ws23',
    'e_weitip_1_ws23'
}


def weekInfo():
    today = datetime.date.today()
    number = today.isocalendar()[1]
    # isWeekend = today.isocalendar()[2]
    # return number
    return 51


def single_request(url):
    data = []
    response = requests.get(url)
    try:
        assert response.status_code == 200
        resp = response.json()["events"]
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
                tasks += future.result()
            except Exception as e:
                print("expection in full_request:{}".format(e))
    
    return dict(t) for t in {tuple(d.items()) for d in tasks}
    


async def search_location(lo):
    await full_request()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(full_request())
    loop.run_until_complete(future)
