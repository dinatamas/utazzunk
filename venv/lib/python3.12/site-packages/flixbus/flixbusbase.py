import requests
from bs4 import BeautifulSoup
import sqlite3
import os
import logging
import requests_cache
import json
import re
from .connection import Connection

from pprint import pprint

requests_cache.install_cache('data/requests_cache.sqlite', allowable_codes=(0, 200, 400, 600), expire_after=3600, response_filter=lambda _: True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class FlixbusBase(object):
    country_url_format = "https://www.flixbus.com/bus/{country}"
    stops = None

    def __init__(self, countries_to_init=["united-kingdom"]):
        if not os.path.exists('data'):
            os.makedirs('data')

        self.conn = sqlite3.connect("data/flixbus_stops.db")
        self.cursor = self.conn.cursor()

        self.create_database()

        # Scrape to get all city names into the DB
        for country in countries_to_init:
            country_stops = self.scrape_stops_of_country(country)
            self.save_stops_to_db(country, country_stops)

        # For each city name find it's ID
        self.get_ids_of_cities()

    def scrape_stops_of_country(self, country_slug):
        response = requests.get(self.country_url_format.format(country=country_slug))
        soup = BeautifulSoup(response.content, 'html.parser')

        stops = []
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            selector = f"#{letter} > ul:nth-child(2) > li > a"
            for stop in soup.select(selector):
                stops.append(stop.text.strip())

        return stops

    def create_database(self):
        # This should be configurable
        # Create table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stops (
                country_name TEXT,
                city_name TEXT,
                city_id TEXT UNIQUE,
                UNIQUE(country_name, city_name)
            )
        ''')

    def save_stops_to_db(self, country, stops):
        # Insert data
        self.cursor.executemany("INSERT OR IGNORE INTO stops (country_name, city_name) VALUES (?, ?)", [(country, stop,) for stop in stops])

        # Commit
        self.conn.commit()

    def get_ids_of_cities(self):
        self.cursor.execute('SELECT city_name FROM stops WHERE city_id IS NULL')
        city_list_db = self.cursor.fetchall()

        if city_list_db:
            logging.info(f"There are {len(city_list_db)} cities without an ID. Going to get these now.")
        else:
            logging.info("All cities have an ID.")

        city_list = [city[0] for city in city_list_db]

        # Fetch and parse bus ID for each city
        for city in city_list:
            try:
                slug = city.lower().replace(' ', '-')
                slug = re.sub(r'[^a-z0-9-]', '', slug)

                url = f"https://www.flixbus.com/bus/{slug}"
                logging.info(f"Getting city id for: {city}")

                response = requests.get(url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    script_content = soup.select('#main-content > script:nth-child(4)')[0].string
                    bus_id = script_content.split('", "')[2]

                    # Update the city entry with the bus_id in the database
                    self.cursor.execute('UPDATE stops SET city_id = ? WHERE city_name = ?', (bus_id, city))
                    self.conn.commit()
            except Exception:
                logging.warning(f"Cannot find city id for: {city} ({url}).")
                pass

    def get_city_id(self, city_name):
        self.cursor.execute('SELECT city_id FROM stops WHERE city_name IS ?', (city_name,))
        city_record = self.cursor.fetchall()
        if city_record:
            return city_record[0][0]

        return None

    def get_connection_data(self, from_stop, to_stop, date="21.07.2023"):
        base_url = "https://global.api.flixbus.com/search/service/v4/search?"

        from_city_id = self.get_city_id(from_stop)
        to_city_id = self.get_city_id(to_stop)

        url = (
            base_url +
            f"from_city_id={from_city_id}&" +
            f"to_city_id={to_city_id}&" +
            f"departure_date={date}&" +
            "products=%7B%22adult%22%3A1%7D&" +
            "currency=EUR&" +
            "locale=nl&" +
            "search_by=cities&" +
            "include_after_midnight_rides=1"
        )

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        parsed_trips = self.parse_content(response.text)

        return parsed_trips

    def parse_content(self, content):
        data = json.loads(content)
        if 'trips' not in data:
            return None

        trips = data['trips']

        parsed_trips = []
        for trip in trips:
            departure_city_id = trip['departure_city_id']
            arrival_city_id = trip['arrival_city_id']
            trip_results = trip['results']

            for _, trip_detail in trip_results.items():
                # TODO This doesn't add all the details yet, like transfers or not.
                departure = trip_detail['departure']
                arrival = trip_detail['arrival']
                price = trip_detail['price']['total']

                parsed_trips.append(
                    Connection(
                        departure['date'],
                        arrival['date'],
                        self.get_city_name(departure_city_id),
                        self.get_city_name(arrival_city_id),
                        departure_city_id,
                        arrival_city_id,
                        price,
                        trip_detail['duration']
                    )
                )

        return parsed_trips

    def get_stops(self):
        if self.stops is not None:
            return self.stops

        self.cursor.execute('SELECT country_name, city_name FROM stops WHERE city_id IS NOT NULL')
        stops_list_db = self.cursor.fetchall()

        stops = {}

        for country, stop in stops_list_db:
            if country in stops:
                stops[country].append(stop)
            else:
                stops[country] = [stop]

        self.stops = stops
        return stops

    def get_city_name(self, city_id):
        self.cursor.execute('SELECT city_name FROM stops WHERE city_id IS ?', (city_id,))
        city_record = self.cursor.fetchall()
        if city_record:
            return city_record[0][0]

        return None
