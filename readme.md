# TimeTable Grabber
scrapped the timetable from electronic faculty ostfalia (spuls API)

because the api was semester based, so in avoid of too many requests every day this program will only refresh one time every day in order to keep the latest timetable. and other requests will only be looked up locally. the newest information every day will be found in files `room\\roomplan-{date}.json`

**StudienArbeit**