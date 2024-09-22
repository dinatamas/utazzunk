from datetime import datetime


class Connection(object):
    def __init__(self, departure_date_time, arrival_date_time, departure_stop, arrival_stop, departure_city_id, arrival_city_id, price, duration=None):
        self.departure_date_time = datetime.fromisoformat(departure_date_time)
        self.arrival_date_time = datetime.fromisoformat(arrival_date_time)
        self.departure_stop = departure_stop
        self.arrival_stop = arrival_stop
        self.departure_city_id = departure_city_id
        self.arrival_city_id = arrival_city_id
        self.price = price
        self.duration = duration

    def duration_str(self):
        if 'days' in self.duration:
            duration_str = f"{self.duration['days']}d {self.duration['hours']}h {self.duration['minutes']}m"
        else:
            duration_str = f"{self.duration['hours']}h {self.duration['minutes']}m"

        return duration_str

    def __str__(self):
        return f"Connection from {self.departure_stop} to {self.arrival_stop} on {self.departure_date_time.strftime('%d-%m-%Y %H:%M')} for {self.price}"

    def to_json(self):
        return {
                "arrival_city": self.arrival_stop,
                "arrival_date_time": self.arrival_date_time.isoformat(),
                "departure_city": self.departure_stop,
                "departure_date_time": self.departure_date_time.isoformat(),
                "duration": self.duration,
                "duration_str": self.duration_str(),
                "price": self.price,
                "string": str(self),
        }

    def has_full_night(self):
        # TODO Calculate this is a bus trip where you could sleep all night, this means at least 6 hours somewhere between 00:00 and 8:00, and no transfers in there.
        pass

    def get_url(self):
        url = f"https://shop.global.flixbus.com/search?departureCity={self.departure_city_id}&arrivalCity={self.arrival_city_id}&rideDate={self.departure_date_time.strftime('%d.%m.%Y')}&adult=1"

        return url
    # https://shop.global.flixbus.com/search?departureCity=3665c7fe-fc24-4b50-9b52-2187944b362c&arrivalCity=40dde3b8-8646-11e6-9066-549f350fcb0c&rideDate=09.11.2023&adult=1
    # TODO Also add distance, and potentially price/distance to this as calculated functions maybe.
