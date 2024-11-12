#!/usr/bin/env python3
from datetime import datetime
import requests

CHEAP_FLIGHTS = 'https://be.wizzair.com/24.10.0/Api/search/CheapFlights'
HEADERS = {
    'User-Agent': 'AppleTV11,1/11.1',
    'Referer': 'https://wizzair.com',
    'x-requestverificationtoken': 'this-can-be-any-value',
    'cookie': 'RequestVerificationToken=this-can-be-any-value',
    'Origin': 'https://wizzair.com',
}

response = requests.post(CHEAP_FLIGHTS, headers=HEADERS, json={
    "departureStation": "BUD",
    "discountedOnly": False,
    "months": 6,
})
print(response.text)

trips = []
for trip in response.json()["items"]:
    # TODO: Check price is actually in HUF!
    date = datetime.strptime(trip["std"], "%Y-%m-%dT%H:%M:%S")
    dest = trip["arrivalStation"]
    price = int(trip["regularOriginalPrice"]["amount"])
    trips.append({"date": date, "dest": dest, "price": price})
trips.sort(key=lambda x: x["date"])
for trip in trips:
    print(f"{trip['date']} - {trip['dest']} - {trip['price']}")

# FLIGHT_DATES = 'https://be.wizzair.com/24.10.0/Api/search/flightDates'
# response = requests.get(FLIGHT_DATES, headers=HEADERS, params={
# "departureStation": "BUD",
# "arrivalStation": "CRL",
# "from": "2024-09-24",
#     "to": "2024-11-24",
# })

print()
print()

FARECHART = 'https://be.wizzair.com/24.10.0/Api/asset/farechart'
response = requests.post(FARECHART, headers=HEADERS, json={
    "isRescueFare": False,
    "adultCount": 1,
    "childCount": 0,
    "dayInterval": 10,
    "wdc": False,
    "isFlightChange": False,
    "flightList": [
        {
            "departureStation": "BUD",
            "arrivalStation": "CRL",
            "date": "2024-11-02",
        },
        {
            "departureStation": "CRL",
            "arrivalStation": "BUD",
            "date": "2024-11-05",
        },
    ]
})

for trip in response.json()["outboundFlights"]:
    date = datetime.strptime(trip["date"], "%Y-%m-%dT%H:%M:%S")
    price = int(trip["price"]["amount"])
    print(f"{date} - {price}")
