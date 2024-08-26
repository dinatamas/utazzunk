#!/usr/bin/env python3
from datetime import datetime, timedelta

from flask import Flask, render_template, request

from utazzunk import (
    get_ryanair,
    get_flixbus,
    format_ryanair,
    format_flixbus,
)


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/getit")
def getit():
    depart_from = datetime.strptime(request.args['depart_from'], "%Y.%m.%d.")
    depart_to = datetime.strptime(request.args['depart_to'], "%Y.%m.%d.")
    arrive_from = datetime.strptime(request.args['arrive_from'], "%Y.%m.%d.")
    arrive_to = datetime.strptime(request.args['arrive_to'], "%Y.%m.%d.")
    ryanair_cutoff = int(request.args["ryanair_cutoff"])
    extended = request.args.get("extended", "nem") == "igen"
    max_dur = timedelta(hours=int(request.args["max_dur"]))
    flixbus_cutoff = int(request.args["flixbus_cutoff"])

    ind = f"{depart_from.strftime('%m.%d.')} - {depart_to.strftime('%m.%d.')}"
    erk = f"{arrive_from.strftime('%m.%d.')} - {arrive_to.strftime('%m.%d.')}"

    if request.args["target"] == "ryanair":
        ryanair = get_ryanair(
            extended=extended,
            cutoff=ryanair_cutoff,
            depart_from=depart_from,
            depart_to=depart_to,
            arrive_from=arrive_from,
            arrive_to=arrive_to,
        )
        return render_template(
            "ryanair.html",
            ryanair=ryanair,
            ind=ind,
            erk=erk,
            kot=f"max. {ryanair_cutoff} Ft",
        )
    else:
        return render_template(
            "flixbus.html",
            ind=ind,
            erk=erk,
            kot=f"max. {flixbus_cutoff} Ft",
            dur=max_dur,
        )
