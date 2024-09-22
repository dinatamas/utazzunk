#!/usr/bin/env python3
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, make_response

from utazzunk import get_ryanair, get_flixbus_reachable


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def index():
    depfrom, depto = request.cookies.get("depart_range", " - ").split(" - ")
    depfrom = depfrom or (datetime.now() + timedelta(days=10)).strftime("%m.%d.")
    depto = depto or (datetime.now() + timedelta(days=11)).strftime("%m.%d.")
    arrfrom, arrto = request.cookies.get("arrive_range", " - ").split(" - ")
    arrfrom = arrfrom or (datetime.now() + timedelta(days=15)).strftime("%m.%d.")
    arrto = arrto or (datetime.now() + timedelta(days=16)).strftime("%m.%d.")
    cutoff = request.cookies.get("cutoff", 20000)
    extended = "checked" if request.cookies.get("extended", "false") == "true" else ""
    maxdur = request.cookies.get("maxdur", 10)
    maxtra = request.cookies.get("maxtra", 1)
    afterwork = request.cookies.get("afterwork", "15:00")
    intfrom, intto = request.cookies.get("interval", " - ").split(" - ")
    intfrom = intfrom or (datetime.now() + timedelta(days=10)).strftime("%m.%d.")
    intto = intto or (datetime.now() + timedelta(days=17)).strftime("%m.%d.")
    mindays = request.cookies.get("mindays", "4")
    maxdays = request.cookies.get("maxdays", "7")

    return render_template(
        "index.html",
        depfrom=depfrom,
        depto=depto,
        arrfrom=arrfrom,
        arrto=arrto,
        extended=extended,
        cutoff=cutoff,
        maxdur=maxdur,
        maxtra=maxtra,
        afterwork=afterwork,
        intfrom=intfrom,
        intto=intto,
        mindays=mindays,
        maxdays=maxdays,
    )


def do_magic(a, b, c):
    cutoff = int(request.args["cutoff"])
    afterwork = request.args["afterwork"]
    now = datetime.now()
    friday = now + timedelta(days=((a - now.weekday()) % 7))
    sunday = friday + timedelta(days=b)
    ryanair = []
    for i in range(12):
        ryanair.extend(get_ryanair(
                depart_from=friday,
                depart_to=friday,
                depart_time=afterwork,
                arrive_from=sunday,
                arrive_to=sunday,
                arrive_time=c,
                cutoff=cutoff,
        ))
        friday += timedelta(days=7)
        sunday += timedelta(days=7)
    return make_response(render_template(
        "ryanair.html",
        ryanair=ryanair,
        depart_range=f"Each week {friday.strftime('%A')} between {afterwork} - 23:59",
        arrive_range=f"Each week {sunday.strftime('%A')} between {c} - 23:59",
        cutoff=cutoff,
    ))


def do_ryanair():
    depart_range = request.args['depart_range'].split(" - ")
    depart_from = _get_date(depart_range[0])
    depart_to = _get_date(depart_range[1])
    arrive_range = request.args['arrive_range'].split(" - ")
    arrive_from = _get_date(arrive_range[0])
    arrive_to = _get_date(arrive_range[1])
    cutoff = int(request.args["cutoff"])
    extended = request.args.get("extended", "false") == "true"
    maxdur = timedelta(hours=int(request.args["maxdur"]))
    maxtra = int(request.args["maxtra"])

    ryanair = get_ryanair(
        depart_from=depart_from,
        depart_to=depart_to,
        arrive_from=arrive_from,
        arrive_to=arrive_to,
        cutoff=cutoff,
        extended=extended,
    )
    resp = make_response(render_template(
        "ryanair.html",
        ryanair=ryanair,
        depart_range=request.args['depart_range'],
        arrive_range=request.args['arrive_range'],
        cutoff=cutoff,
    ))
    return resp


def do_flixbus():
    depart_range = request.args['depart_range'].split(" - ")
    depart_from = _get_date(depart_range[0])
    depart_to = _get_date(depart_range[1])
    arrive_range = request.args['arrive_range'].split(" - ")
    arrive_from = _get_date(arrive_range[0])
    arrive_to = _get_date(arrive_range[1])
    cutoff = int(request.args["cutoff"])
    extended = request.args.get("extended", "false") == "true"
    maxdur = timedelta(hours=int(request.args["maxdur"]))
    maxtra = int(request.args["maxtra"])

    resp = make_response(render_template(
        "flixbus.html",
        depart_range=request.args['depart_range'],
        arrive_range=request.args['arrive_range'],
        cutoff=cutoff,
        maxdur=maxdur,
        maxtra=maxtra,
    ))
    return resp


def do_holiday():
    interval = request.args['interval'].split(" - ")
    intfrom = _get_date(interval[0])
    intto = _get_date(interval[1])
    mindays = int(request.args["mindays"])
    maxdays = int(request.args["maxdays"])
    cutoff = int(request.args["cutoff"])
    extended = request.args.get("extended", "false") == "true"

    ryanair = []
    delta = (intto - intfrom).days - mindays
    for i in range(delta):
        arrfrom = intfrom + timedelta(i+mindays)
        arrto = min(intfrom + timedelta(i+maxdays), intto)
        ryanair.extend(get_ryanair(
            depart_from=intfrom + timedelta(days=i),
            depart_to=intfrom + timedelta(days=i),
            arrive_from=arrfrom,
            arrive_to=arrto,
            cutoff=cutoff,
            extended=extended,
        ))
    resp = make_response(render_template(
        "ryanair.html",
        ryanair=ryanair,
        depart_range=f"{request.args['interval']} ({mindays} - {maxdays} nap)",
        arrive_range=request.args['interval'],
        cutoff=cutoff,
    ))
    return resp


@app.route("/getit")
def getit():
    if request.args["target"] == "ryanair":
        resp = do_ryanair()

    if request.args["target"] == "flixbus":
        resp = do_flixbus()

    if request.args["target"] == "magic_weekend":
        resp = do_magic(11, 2, "15:00")
    if request.args["target"] == "magic_weekend_friday":
        resp = do_magic(10, 3, "00:00")
    if request.args["target"] == "magic_weekend_monday":
        resp = do_magic(11, 3, "00:00")

    if request.args["target"] == "holiday":
       resp = do_holiday()

    resp = _set_cookies(resp)
    return resp


@app.route("/flixconf")
def flixconf():
    CITIES, COUNTRIES = get_flixbus_reachable()
    resp = make_response(render_template(
        "orszagok.html",
        COUNTRIES=COUNTRIES,
    ))
    return resp


def _get_date(date):
    date = datetime.strptime(date, "%m.%d.")
    date = date.replace(year=datetime.now().year)
    if date < datetime.now():
        date += timedelta(year=1)
    return date


def _set_cookies(resp):
    for name, value in request.args.items():
        resp.set_cookie(name, value)
    if "extended" not in request.args:
        resp.set_cookie("extended", "false")
    return resp
