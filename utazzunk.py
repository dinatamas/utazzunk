#!/usr/bin/env python3
import argparse
from datetime import datetime, timedelta
from operator import attrgetter

import requests
from flixbus import Flixbus
from ryanair import Ryanair
from tqdm import tqdm


RYANAIR_CUTOFF = 40_000
FLIXBUS_CUTOFF = 15_000

DEPART_FROM = datetime(2024, 9, 24)
DEPART_TO = datetime(2024, 9, 25)
ARRIVE_FROM = datetime(2024, 9, 28)
ARRIVE_TO = datetime(2024, 9, 29)

MAX_DUR = timedelta(hours=10)

# Less popular Flixbus destinations to still include
INTERESTING_CITIES = ["Kotor"]


#
# Overwrite everything with a database.
#
class SuperFlixbus(Flixbus):
    def __init__(self):
        pass

    def get_connection_data(self, from_id, to_id, date):
        base_url = "https://global.api.flixbus.com/search/service/v4/search?"
        url = (
            base_url +
            f"from_city_id={from_id}&" +
            f"to_city_id={to_id}&" +
            f"departure_date={date}&" +
            "products=%7B%22adult%22%3A1%7D&" +
            "currency=HUF&" +
            "locale=hu&" +
            "search_by=cities&" +
            "include_after_midnight_rides=0"
        )
        response = requests.get(url, timeout=3)
        parsed_trips = self.parse_content(response.text)
        # Filter sold out trips.
        good_trips = list()
        for trip in parsed_trips:
            if trip.price == 0:
                continue
            good_trips.append(trip)
        return good_trips

    def get_city_name(self, city_id):
        return city_id


def get_flixbus(
        cutoff=FLIXBUS_CUTOFF,
        depart_from=DEPART_FROM,
        depart_to=DEPART_TO,
        arrive_from=ARRIVE_FROM,
        arrive_to=ARRIVE_TO,
    ):
    FLIXBUS_URL = "https://global.api.flixbus.com"
    BUDAPEST = "40de6527-8646-11e6-9066-549f350fcb0c"
    REACHABLE_URL = f"{FLIXBUS_URL}/cms/cities/{BUDAPEST}/reachable"
    PARAMS = {"language": "hu", "limit": 1000, "currency": "HUF"}
    response = requests.get(REACHABLE_URL, params=PARAMS).json()

    CITIES = list()
    COUNTRIES = dict()
    for c in response["result"]:
        if c["country"] == "HU":
            continue
        if "repülőtér" in c["name"]:
            continue
        # "Less interesting" destinations with many Flixbus stations.
        if c["name"] not in INTERESTING_CITIES:
            if c["country"] in ("HR", "SK", "RO", "PL"):
                if c["search_volume"] < 50_000:
                    continue
        if "price" in c:
            if c["price"]["HUF"]["min"] < cutoff:
                CITIES.append(c)
                COUNTRIES[c["country"]] = COUNTRIES.get(c["country"], []) + [c]

    api = SuperFlixbus()

    best = []
    for city in tqdm(CITIES, leave=False):
        name = city["name"]
        if "Parndorf" in name:
            name = "Parndorf"
        try:
            start = depart_from.strftime("%d-%m-%Y")
            end = depart_to.strftime("%d-%m-%Y")
            lbest = api.get_cheapest_for_range(start, end, BUDAPEST, city["uuid"])
            if lbest.price < cutoff:
                start = arrive_from.strftime("%d-%m-%Y")
                end = arrive_to.strftime("%d-%m-%Y")
                rbest = api.get_cheapest_for_range(start, end, BUDAPEST, city["uuid"])
                total = int(lbest.price + rbest.price)
                if total < cutoff * 2:
                    ltime = lbest.departure_date_time.strftime("%m.%d. %H:%M")
                    ldur = lbest.arrival_date_time - lbest.departure_date_time
                    rtime = rbest.departure_date_time.strftime("%m.%d. %H:%M")
                    rdur = rbest.arrival_date_time - rbest.departure_date_time
                    if ldur > MAX_DUR or rdur > MAX_DUR:
                        continue
                    best.append(
                        (
                            total,
                            name,
                            city["country"],
                            f"{ltime} ({str(ldur)})",
                            f"{rtime} ({str(rdur)})",
                        )
                    )
        except Exception:
            pass
    return sorted(best)


def get_ryanair(
        extended=False,
        cutoff=RYANAIR_CUTOFF,
        depart_from=DEPART_FROM,
        depart_to=DEPART_TO,
        arrive_from=ARRIVE_FROM,
        arrive_to=ARRIVE_TO,
    ):
    api = Ryanair("HUF")
    airports = ["BUD", "BTS", "VIE"] if extended else ["BUD"]
    best = dict()
    for airport in airports:
        trips = api.get_cheapest_return_flights(
            airport,
            depart_from,
            depart_to,
            arrive_from,
            arrive_to,
        )
        for trip in trips:
            dest = trip.outbound.destination
            if dest not in best:
                best[dest] = [trip.outbound, trip.inbound]
            else:
                # Calculate outbound.
                curr, prev = trip.outbound, best[dest][0]
                cheaper = min(curr, prev, key=attrgetter("price"))
                pricier = max(curr, prev, key=attrgetter("price"))
                if pricier.origin == "BUD":
                    if pricier.price - cheaper.price > 10000:
                        cheaper, pricier = pricier, cheaper
                best[dest][0] = cheaper

                # Calculate inbound
                curr, prev = trip.inbound, best[dest][1]
                cheaper = min(curr, prev, key=attrgetter("price"))
                pricier = max(curr, prev, key=attrgetter("price"))
                if pricier.destination == "BUD":
                    if pricier.price - cheaper.price > 10000:
                        cheaper, pricier = pricier, cheaper
                best[dest][1] = cheaper
    best = dict(sorted(best.items(), key=lambda t: t[1][0].price + t[1][1].price))
    best = [t for t in best.values() if t[0].price + t[1].price < cutoff]
    return best


def main():
    args = parse_args()

    best = get_ryanair(extended=args.A)
    print()
    print("===== RYANAIR =====")
    print()
    if best:
        tprint(
            ["Price", "Destination", "From", "Leave", "To", "Return"],
            *[
                [
                    t[0].price + t[1].price,
                    t[0].destinationFull,
                    t[0].origin,
                    t[0].departureTime.strftime("%m.%d. %H:%M"),
                    t[1].destination,
                    t[1].departureTime.strftime("%m.%d. %H:%M"),
                ] for t in best
            ]
        )
    else:
        print("No destinations are cheap enough")
    print()

    best = get_flixbus()
    print("===== FLIXBUS =====")
    print()
    tprint(
        ["Price", "Destination", "Leave", "Return"],
        *[
            [
                price,
                f"{name} ({country})",
                dep,
                ret,
            ] for price, name, country, dep, ret in best
        ]
    )
    #if args.s:
    #    print("Stats:")
    #    for name, cities in sorted(COUNTRIES.items()):
    #        print(f"  - {name}: {len(cities)}")
    #    print()
    #if args.c:
    #    for name, cities in sorted(COUNTRIES.items()):
    #        print()
    #        print(f"### {name}: ###")
    #        for c in cities:
    #            print(f"   {c['name']} ({c['slug']}) - {c['price']['HUF']['min']}")
    #    print()
    print()


def tprint(*rows):
    if isinstance(rows[0], str):
        rows = [[rows[0]], *[[r] for r in rows[1:]]]
    newrows = []
    for row in rows:
        newcols = [cell if isinstance(cell, list) else [cell] for cell in row]
        longest = max(len(col) for col in newcols)
        newcols = [col + [" ..."] * (longest - len(col)) for col in newcols]
        for i in range(longest):
            newcells = [str(col[i]) for col in newcols]
            newrows.append(newcells)
    rows = newrows
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in [rows[0], ["-" * len(header) for header in rows[0]], *rows[1:]]:
        print("   " + "  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-A", action="store_true", help="include BTS+VIE airports too")
    #parser.add_argument("-c", action="store_true", help="print Flixbus cities")
    #parser.add_argument("-s", action="store_true", help="print Flixbus stats")
    return parser.parse_args()


if __name__ == "__main__":
    main()


#
# TODO:
#   - Compare Flixbus prices to BTS and VIE for connections
#   - Get all Flixbus destinations from Budapest
#   - Find way to search inbound flights.
#   - Alternatives for multiple airports.
#   - Alternatives for dates: +/- days for how much?
#   - Better date ranges + validate them
#   - Add WizzAir!
#

#
# Transform to Javascript:
#   - https://github.com/juliuste/flix
#   - https://github.com/2BAD/ryanair
# This way we could create a client-only website!
#

# TODO: Intermodality!
# Check for both Flixbus and Ryanair...

# - https://global.flixbus.com/bus/budapest
# - Click on "Show more bus routes"
# - Check destinations from Budapest 

# https://global.api.flixbus.com/cms/cities/40de6527-8646-11e6-9066-549f350fcb0c/reachable?language=hu&limit=5&currency=HUF
# https://global.api.flixbus.com/search/service/v4/search?from_city_id=40de6527-8646-11e6-9066-549f350fcb0c&to_city_id=d03c34f4-0b2c-42de-b5c6-792eedcd9cfb&departure_date=25.08.2024&products=%7B%22adult%22%3A1%7D&currency=EUR&locale=en&search_by=cities&include_after_midnight_rides=1&disable_distribusion_trips=0
# https://global.api.flixbus.com/search/service/cities/details?locale=en&from_city_id=13938
# https://global.api.flixbus.com/search/autocomplete/cities?q=Salzburg&lang=en&country=en&flixbus_cities_only=false&stations=true&popular_stations=true
