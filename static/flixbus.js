function getDate(date) {
  date = new Date(Date.parse(date))
  date.setYear(new Date().getFullYear())
  if (date < new Date()) {
    date.setFullYear(new Date().getFullYear() + 1)
  }
  return date
}

async function getBest(from, to, a, b, MAXTRA, MAXDUR) {
    best_trip = null
    for (var d = new Date(from.getTime()); d <= to; d.setDate(d.getDate() + 1)) {
      day = ("0" + d.getDate()).slice(-2)
      month = ("0" + (d.getMonth() + 1)).slice(-2)
      year = d.getFullYear()
      dt = `${day}.${month}.${year}`

      url = "https://global.api.flixbus.com/search/service/v4/search?"
      url += `from_city_id=${a}`
      url += `&to_city_id=${b}`
      url += `&departure_date=${dt}`
      url += "&products=%7B%22adult%22%3A1%7D"
      url += "&currency=HUF"
      url += "&locale=hu"
      url += "&search_by=cities"
      url += "&include_after_midnight_rides=1"

      try {
          response = await fetch(url, { signal: AbortSignal.timeout(4000) })
          result = await response.json()
      } catch (err) {
          console.log(err)
          console.dir(err)
          continue
      }

      for (trips of result.trips) {
        for (trip of Object.entries(trips.results)) {
          trip = trip[1]
          if (trip.status !== "available") { continue }
          if (trip.legs.length-1 > MAXTRA) { continue }
          if (trip.duration.hours > MAXDUR) { continue }
          if (trip.price.total == 0) { continue }
          if (best_trip == null || best_trip.price.total > trip.price.total) {
            best_trip = trip
          }
        }
      }
    }
    return best_trip
}

function renderTable(RESULTS) {

    function renderTrip(trip) {
        
    }

    function compareTrips(a, b) { return a[1] > b[1] ? 1 : -1 }
    RESULTS.sort(compareTrips)

    document.getElementById("mytable").innerHTML = ''

    for (result of RESULTS) {

	name = result[0]
	price = result[1]
	city = result[2]
	best_depart = result[3]
	best_arrive = result[4]

        dest = document.createElement("tr")

        tdprice = document.createElement("td")
        tdprice.textContent = `${price} Ft`
        dest.appendChild(tdprice)

        tddest = document.createElement("td")
        tddest.textContent = `${name} (${city.country})`
        dest.appendChild(tddest)

        tdleave = document.createElement("td")
        dep = new Date(Date.parse(best_depart.departure.date))
        day = ("0" + dep.getDate()).slice(-2)
        month = ("0" + (dep.getMonth() + 1)).slice(-2)
        hour = ("0" + (dep.getHours() + 1)).slice(-2)
        minute = ("0" + (dep.getMinutes() + 1)).slice(-2)
        dt = `${month}.${day}. ${hour}:${minute}`
        hours = ("0" + (best_depart.duration.hours)).slice(-2)
        mins = ("0" + (best_depart.duration.minutes)).slice(-2)
        dtt = `${hours}:${mins}`
        tra = best_depart.legs.length > 1 ? ` - ${best_depart.legs.length-1} átszállás` : ""
        tdleave.textContent = `${dt} (${dtt} h) ${tra}`
        dest.appendChild(tdleave)

        tdarrive = document.createElement("td")
        arr = new Date(Date.parse(best_arrive.departure.date))
        day = ("0" + arr.getDate()).slice(-2)
        month = ("0" + (arr.getMonth() + 1)).slice(-2)
        hour = ("0" + (arr.getHours() + 1)).slice(-2)
        minute = ("0" + (arr.getMinutes() + 1)).slice(-2)
        dt = `${month}.${day}. ${hour}:${minute}`
        hours = ("0" + (best_arrive.duration.hours)).slice(-2)
        mins = ("0" + (best_arrive.duration.minutes)).slice(-2)
        dtt = `${hours}:${mins}`
        tra = best_arrive.legs.length > 1 ? ` - ${best_arrive.legs.length-1} átszállás` : ""
        tdarrive.textContent = `${dt} (${dtt} h) ${tra}`
        dest.appendChild(tdarrive)

        document.getElementById("mytable").appendChild(dest)
    }
}

async function doFlixbus() {
  query = window.location.search
  params = new URLSearchParams(query)
  depart_range = params.get("depart_range").split(" - ")
  depart_from = getDate(depart_range[0])
  depart_to = getDate(depart_range[1])
  arrive_range = params.get("arrive_range").split(" - ")
  arrive_from = getDate(arrive_range[0])
  arrive_to = getDate(arrive_range[1])

  CUTOFF = parseInt(params.get("cutoff"))
  MAXDUR = parseInt(params.get("maxdur"))
  MAXTRA = parseInt(params.get("maxtra"))

  FLIXBUS = "https://global.api.flixbus.com"
  BUDAPEST = "40de6527-8646-11e6-9066-549f350fcb0c"
  REACHABLE = `${FLIXBUS}/cms/cities/${BUDAPEST}/reachable`
  response = await fetch(`${REACHABLE}?` + new URLSearchParams({
    "language": "hu",
    "limit": 1000,
    "currency": "HUF",
  }).toString())
  result = await response.json()
  CITIES = []
  COUNTRIES = {}
  INTERESTING = ["Kotor"]

  for (trip of result.result) {
    if (trip.country == "HU") { continue }
    if (trip.name.toLowerCase().includes("repülőtér")) { continue }
    if (!INTERESTING.includes(trip.name)) {
      if (["HR", "SK", "RO", "PL"].includes(trip.country)) {
        if (trip.search_volume < 50000) { continue }
      }
    }
    // trip.price.min is not accurate, there are sometimes cheaper options
    // than shown there, so we cannot filter based on that... but we could
    // sort the CITIES based on popularity AND (average / min) affordability
    CITIES.push(trip)
  }

  RESULTS = []
  for (i in CITIES) {
    city = CITIES[i]
    name = city.name
    if (name.includes("Parndorf")) { name = "Parndorf" }
    j = parseInt(i) + 1
    text = `Most töltődik: ${name} (${j} / ${CITIES.length})`
    document.getElementById("myp").textContent = text

    best_depart = await getBest(depart_from, depart_to, BUDAPEST, city.uuid, MAXTRA, MAXDUR)
    best_arrive = await getBest(arrive_from, arrive_to, city.uuid, BUDAPEST, MAXTRA, MAXDUR)

    if (best_depart !== null && best_arrive !== null) {
      price = best_depart.price.total + best_arrive.price.total
      if (price <= CUTOFF) {
        RESULTS.push([name, price, city, best_depart, best_arrive])
      }
    }
    renderTable(RESULTS)
  }

  document.getElementById("myp").textContent = `Összes betöltve!`

  return response
}

// doFlixbus()
