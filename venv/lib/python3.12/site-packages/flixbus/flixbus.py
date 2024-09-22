from .flixbusbase import FlixbusBase
from datetime import datetime, timedelta
from pprint import pprint


class Flixbus(FlixbusBase):
    """
    Flixbus easy to use programmable interface.

    This class does more high level stuff. For the underlying logic look in FlixbusBase.
    """

    def __init__(self, countries_to_init=["united-kingdom"]):
        super().__init__(countries_to_init)

    def get_cheapest_per_day_for_range(self, start_date, end_date, from_stop, to_stop):
        start_date = datetime.strptime(start_date, "%d-%m-%Y")
        end_date = datetime.strptime(end_date, "%d-%m-%Y")

        date_range = [start_date + timedelta(days=x) for x in range(0, (end_date-start_date).days + 1)]

        cheapest_per_date = []
        for date in date_range:
            formatted_date = date.strftime("%d.%m.%Y")
            connections = self.get_connection_data(from_stop, to_stop, formatted_date)

            if len(connections):
                cheapest_connection = sorted(connections, key=lambda connection: connection.price)[0]

                cheapest_per_date.append(cheapest_connection)

        return cheapest_per_date

    def get_cheapest_for_range(self, start_date, end_date, from_stop, to_stop):
        cheapest_per_date = self.get_cheapest_per_day_for_range(start_date, end_date, from_stop, to_stop)
        cheapest_connection = sorted(cheapest_per_date, key=lambda connection: connection.price)[0]
        
        return cheapest_connection


if __name__ == "__main__":
    fb = Flixbus(['united-kingdom'])
    cheapest = fb.get_cheapest_for_range("01-11-2023", "01-12-2023", "Cambridge", "London")
    pprint(cheapest)
