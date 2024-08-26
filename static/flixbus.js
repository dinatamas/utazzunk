async function doFlixbus() {
  query = window.location.search
  params = new URLSearchParams(query)
  depart_from = new Date(Date.parse(params.get("depart_from")))
  depart_to = new Date(Date.parse(params.get("depart_to")))
  arrive_from = new Date(Date.parse(params.get("arrive_from")))
  arrive_to = new Date(Date.parse(params.get("arrive_to")))

  CUTOFF = parseInt(params.get("flixbus_cutoff"))

  FLIXBUS = "https://global.api.flixbus.com"
  BUDAPEST = "40de6527-8646-11e6-9066-549f350fcb0c"
  REACHABLE = `${FLIXBUS}/cms/cities/${BUDAPEST}/reachable`
  response = await fetch(`${REACHABLE}?` + new URLSearchParams({
    "language": "hu",
    "limit": 1000,
    "currency": "HUF",
  }).toString())
  result = await response.json()
  count = result.count
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
    if ("price" in trip) {
      if (trip.price.HUF.min < CUTOFF * 0.7) {
        CITIES.push(trip)
      }
    }
  }
  console.log(CITIES)

  search = "https://global.api.flixbus.com/search/service/v4/search?"

  for (city of CITIES) {

    name = city.name
    if (name.includes("Parndorf")) { name = "Parndorf" }

    document.getElementById("myp").textContent = `Most töltődik: ${name} ...`

    best_depart = null
    for (var d = new Date(depart_from.getTime()); d <= depart_to; d.setDate(d.getDate() + 1)) {
      day = ("0" + d.getDate()).slice(-2)
      month = ("0" + (d.getMonth() + 1)).slice(-2)
      year = d.getFullYear()
      dt = `${day}.${month}.${year}`

      url = search
      url += `from_city_id=${BUDAPEST}`
      url += `&to_city_id=${city.uuid}`
      url += `&departure_date=${dt}`
      // TODO: Allow setting different categories.
      url += "&products=%7B%22adult%22%3A1%7D"
      url += "&currency=HUF"
      url += "&locale=hu"
      url += "&search_by=cities"
      url += "&include_after_midnight_rides=0"

      response = await fetch(url, { signal: AbortSignal.timeout(3000) })
      result = await response.json()
      console.log(result)

      for (trips of result.trips) {
        for (trip of Object.entries(trips.results)) {
          trip = trip[1]
          // TODO: Check things like transfers.
          if (best_depart == null || best_depart.price.total > trip.price.total) {
            best_depart = trip
          }
        }
      }
    }

    best_arrive = null
    for (var d = new Date(arrive_from.getTime()); d <= arrive_to; d.setDate(d.getDate() + 1)) {
      day = ("0" + d.getDate()).slice(-2)
      month = ("0" + (d.getMonth() + 1)).slice(-2)
      year = d.getFullYear()
      dt = `${day}.${month}.${year}`

      url = search
      url += `from_city_id=${BUDAPEST}`
      url += `&to_city_id=${city.uuid}`
      url += `&departure_date=${dt}`
      // TODO: Allow setting different categories.
      url += "&products=%7B%22adult%22%3A1%7D"
      url += "&currency=HUF"
      url += "&locale=hu"
      url += "&search_by=cities"
      url += "&include_after_midnight_rides=0"

      response = await fetch(url, { signal: AbortSignal.timeout(3000) })
      result = await response.json()
      console.log(result)

      for (trips of result.trips) {
        for (trip of Object.entries(trips.results)) {
          trip = trip[1]

          // TODO: Check things like transfers.
          if (best_arrive == null || best_arrive.price.total > trip.price.total) {
            best_arrive = trip
          }
        }
      }
    }

    // dest = document.createElement("div")
    // price = (best_depart !== null && best_arrive !== null)
    // ? `${best_depart.price.total + best_arrive.price.total}` : `null`
    // dest.textContent = `${name} (${city.country}) = ${price}`

    if (best_depart !== null && best_arrive !== null) {
      price = best_depart.price.total + best_arrive.price.total
      if (price <= CUTOFF) {

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
        tdleave.textContent = `${dt} (${dtt} h)`
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
        tdarrive.textContent = `${dt} (${dtt} h)`
        dest.appendChild(tdarrive)

        document.getElementById("mydiv").appendChild(dest)

        // TODO: List too expensive destinations!

      }

    }

  }

  document.getElementById("myp").textContent = `Összes betöltve!`

  return response
}
doFlixbus()
