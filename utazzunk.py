#!/usr/bin/env python3
import argparse
from datetime import datetime
from operator import attrgetter

from ryanair import Ryanair


class SuperRyanair(Ryanair):
    def supersearch(
        self,
        airports,
        leave_from,
        leave_to,
        return_from,
        return_to,
    ):
        best = dict()
        for airport in airports:
            trips = self.get_cheapest_return_flights(
                airport,
                leave_from,
                leave_to,
                return_from,
                return_to,
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

    leave_from = datetime(2024, 3, 10)
    leave_to = datetime(2024, 3, 11)
    return_from = datetime(2024, 3, 15)
    return_to = datetime(2024, 3, 16)

    best = api.supersearch(airports, leave_from, leave_to, return_from, return_to)
    best = [t for t in best.values() if t[0].price + t[1].price < 40000]

    print()
    tprint(
        ["Price", "Destination", "From", "Leave", "To", "Return"],
        *[
            [
                t[0].price + t[1].price,
                t[0].destinationFull.split(",")[0],
                t[0].origin,
                t[0].departureTime.strftime("%m.%d. %H:%M"),
                t[1].destination,
                t[1].departureTime.strftime("%m.%d. %H:%M"),
            ] for t in best
        ]
    )


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
#   - Better date ranges.
#   - Add WizzAir!
#
