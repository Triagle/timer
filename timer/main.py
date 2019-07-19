from flask import Blueprint, render_template, request, abort
from datetime import datetime, timedelta
import json
from collections import defaultdict
import re
import random
from timer.model import Entry, Project, EntryEncoder, db, decode_entry, format_delta
from flask_login import login_required

main = Blueprint("main", __name__)


@main.route("/entries")
def entries():
    return json.dumps(Entry.query.all(), cls=EntryEncoder)


def new_project(name):
    red = random.randint(128, 255)
    green = random.randint(128, 255)
    blue = random.randint(128, 255)
    return Project(name=name, colour_red=red, colour_green=green, colour_blue=blue)


@main.route("/add", methods=["POST"])
def add_entry():
    text = json.loads(request.data)["data"]
    match = re.search(r"#(\w+)", text)
    project = None
    name = text
    if match is not None:
        project_query = Project.query.filter(Project.name == match.group(1))
        if project_query.count() > 0:
            project = project_query.first()
        else:
            project = new_project(match.group(1))
        name = text[: match.start()].rstrip() + " " + text[match.end() :].lstrip()

    db.session.add(Entry(name=name, start=datetime.now(), end=None, project=project))
    db.session.commit()
    return json.dumps({"status": "ok"})


@main.route("/delete/<id>", methods=["DELETE"])
def delete(id):
    Entry.query.filter_by(id=id).delete()
    db.session.commit()


@main.route("/stop", methods=["post"])
def stop():
    data = json.loads(request.data, object_hook=decode_entry)
    entry = Entry.query.get(data["id"])
    entry.end = data["end"]
    db.session.commit()
    return json.dumps({"status": "ok"})


@main.route("/edit/<id>")
def edit(id):
    entry = Entry.query.get(id)
    if entry is not None:
        return render_template("edit.html", entry=entry)
    else:
        abort(404)


@main.route("/update", methods=["put"])
def update():
    data = json.loads(request.data, object_hook=decode_entry)

    if data["end"] < data["start"] or data["name"] == "":
        return json.dumps({"status": "invalid update"})

    entry = Entry.query.get(data["id"])
    entry.name = data["name"]
    if data["project"] == "":
        entry.project = None
    elif entry.project:
        entry.project.name = data["project"]
    else:
        entry.project = new_project(data["project"])

    entry.start = data["start"]
    entry.end = data.get("end", entry.end)
    db.session.commit()
    return json.dumps({"status": "ok"})


@main.route("/")
@login_required
def index():
    total_duration = timedelta()
    clocked_hours = defaultdict(timedelta)
    filter = request.args.get("filter")
    period = "all time"
    entries = []
    if filter == "today":
        entries = Entry.query.filter(Entry.start >= datetime.now().date()).all()
        period = "today"
    elif filter == "week":
        today = datetime.now().date()
        start_week = today - timedelta(days=today.weekday())
        entries = Entry.query.filter(Entry.start >= start_week).all()
        period = "this week"
    else:
        entries = Entry.query.all()

    for entry in entries:
        if entry.end is not None:
            total_duration += entry.duration
            clocked_hours[entry.start.date()] += entry.duration

    return render_template(
        "index.html",
        entries=entries,
        total_duration=format_delta(total_duration, include_days=True),
        clocked_hours={k: format_delta(d) for k, d in clocked_hours.items()},
        period=period,
    )
