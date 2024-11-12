# Utazzunk Olcsón!!

- `flask --app app run --debug --host 0.0.0.0 --port 80`

## Ötletgyűjtemény

* Wizzair support hozzáadása
* Óra beállítás (délután / este)
* TLS certificate install (lestencrypt / certbot)
* Deploy behind uwsgi / Nginx

* Háttérban futó process -> JSON file -> best deals -> notifications
* Hétvégi quick-gomb: ne legyen túl hosszú a repülés
  * Péntek délután / este indulás -> vasárnap este visszaérkezés
  * Következő három hónap bármelyik hétvégéje
  * Ryanair -> Any destination + Flexible dates + Fri + 3 days (pick a month)
    * Then you can filter for flight duration and departure times as well
* Ryanair -> utazási idő kijelzése + szűrés
* Őszi szünet quick-gomb: hosszú két hetes perióduson belül 4-5-6-7 nap
* Ár-érték arány bevezetése: Izland 33k is jó, de Milánó 20k is rossz...
  * Nagyon jó ajánlatok relatíve olcsón
    * pl. Izland, Isztambul... -> Google Flights trendek?
* Város / országszűrő

https://medium.com/@yusufkaratoprak/1a2f33f86867 - nginx+letsencrypt

```python
@app.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)
```

- `flask --app app --debug run`

https://github.com/krisukox/google-flights-api
