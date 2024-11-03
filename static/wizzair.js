
async function doWizzair() {

    CHEAP_FLIGHTS = 'https://be.wizzair.com/24.10.0/Api/search/CheapFlights'

    response = await fetch(`${CHEAP_FLIGHTS}`,
    {
        method: 'POST',
        mode: 'no-cors',
        headers: {
//            "user-agent": "AppleTV11,1/11",
//            "origin": "https://wizzair.com",
//            "referrer": "https://wizzair.com",
            "content-type": "application/json",
        },
        body: JSON.stringify({
            "departureStation": "BUD",
            "discountedOnly": false,
            "months": 6,
        })
    })
    result = await response.json()

//         headers: { HEADERS }
    for (res of result) {

    trip = document.createElement("tr")

    date = document.createElement("td")
    date.textContent = `${res.std}`
    trip.appendChild(date)

    dest = document.createElement("td")
    trip.appendChild(dest)

    price = document.createElement("td")
    trip.appendChild(price)

    document.getElementById("mytable").appendChild(trip)

    }

}
