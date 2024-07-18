#!/usr/bin/env python3
import argparse
from datetime import datetime
from operator import attrgetter

from ryanair import Ryanair


CHEAP_CUTOFF = 100_000

LEAVE_FROM = datetime(2024, 8, 24)
LEAVE_TO = datetime(2024, 8, 25)
RETURN_FROM = datetime(2024, 8, 26)
RETURN_TO = datetime(2024, 8, 27)


class SuperRyanair(Ryanair):
    def supersearch(self, airports):
        best = dict()
        for airport in airports:
            trips = self.get_cheapest_return_flights(
                airport,
                LEAVE_FROM,
                LEAVE_TO,
                RETURN_FROM,
                RETURN_TO,
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
        return best


def main():
    args = parse_args()

    api = SuperRyanair("HUF")

    airports = ("BUD", "BTS", "VIE") if args.A else ("BUD",)

    #
    # Note: when there is no overlap between leave and return,
    # the best return flights are also the best individual
    # inbound and outbound flights separately.
    #

    best = api.supersearch(airports)
    best = [t for t in best.values() if t[0].price + t[1].price < CHEAP_CUTOFF]

    print()
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
    return parser.parse_args()


if __name__ == "__main__":
    main()


#
# TODO:
#   - Find way to search inbound flights.
#   - Alternatives for multiple airports.
#   - Alternatives for dates: +/- days for how much?
#   - Better date ranges + validate them
#   - Add WizzAir!
#
