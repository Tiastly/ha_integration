# ePlateController

**StudienArbeit**

# 🚧still in working🚧

this is a Homeassistant integration, combine with an esp32 and Display to use (where is it, idk😴), so we could say, this part is an information-gather and publisher (MQTT)

the information consist of 3 parts, 
- **lecture information**: the Schedule table from electronic faculty Ostfalia (SpulseEins API)
> because the api was semester based, so in avoid of too many requests every day this program will only refresh one time every day in order to keep the latest timetable. and other requests will only be looked up locally. the newest information every day will be found in files `room\\roomplan-{date}.json`
- partly **text descriptions** or url
  user input

- more **text** in office-mode

- **sensors**
  user select, must first be added in Homeassistant

  ⚠ check the **type of sensor** `sensor device classes` before you add other sensors, otherwise it could  probably not be showed

# todo

- [x] add: multiple device
- [x] add: cmd_control
- [x] sensor select&display with type name
- [x] fix: restart and keep data
- [x] update: selectable classroom rather text
- [x] update: room not repeatable -> cannot create same room with same unique Id
- [x] add: move cmd_control to ButtonEntity so that repeatable 
- [x] add: additionally message block for office type 
- [ ] fix: illegal Manual entry-code 
- [x] fix: keep member after restart
- [x] fix: msg payload

- [x] fix: empty text
- [x] fix: entity struct
- [x] update: member payload
- [x] UI Guide
  - [x] update: Modiauswahl 
  - [x] add: Sensorauswahl

- [x] add: add device manually
- [x] add: device status
- [ ] test files

~~Studienarbeit verfassen~~


# Usage
- download and put it in your `custom-component` files
- check your MQTT-Broker is running
- restart the Homeassistant to load this
- find where is the Hardware part, and run it
- ~~be a Mitarbeiter von Elektrotechnik Fakultät der Ostfalia~~ 
- enjoy

# Features
- MQTT-Discovery
- Integration UI supported
- classroom and office mode supported
- useless (so far)

> thx all the other developers, that give me a lot of references, truly
> ---from a noob🥰
