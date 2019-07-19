from flask import Flask, render_template, request, abort
from datetime import datetime, timedelta
import json
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy
import re
import random


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"  # CHANGE ME!!!
db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    colour_red = db.Column(db.Integer, nullable=False)
    colour_blue = db.Column(db.Integer, nullable=False)
    colour_green = db.Column(db.Integer, nullable=False)


def format_delta(delta, include_days=False):
    seconds = int(delta.total_seconds())

    if include_days is True:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        mins = (seconds % 3600) // 60
        return f"{days}:{hours:02}:{mins:02}"

    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    return f"{hours:02}:{mins:02}"


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    project = db.relationship("Project", backref=db.backref("entries", lazy=True))

    @property
    def human_duration(self):
        return format_delta(self.duration)

    @property
    def duration(self):
        return self.end - self.start

    @property
    def ongoing_human_duration(self):
        return format_delta(datetime.now() - self.start)


class EntryEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Entry):
            return {
                "id": o.id,
                "name": o.name,
                "start": o.start,
                "end": o.end,
                "project": o.project,
                "duration": o.duration.total_seconds() if o.end is not None else None,
                "human_duration": o.human_duration if o.end is not None else None,
            }
        elif isinstance(o, Project):
            return {
                "id": o.id,
                "name": o.name,
                "colour": f"rgb({o.colour_red}, {o.colour_green}, {o.colour_blue}, 1)",
            }
        elif isinstance(o, datetime):
            return {
                "year": o.year,
                "month": o.month,
                "day": o.day,
                "hour": o.hour,
                "minute": o.minute,
                "second": o.second,
            }
        return super().default(o)


@app.route("/entries")
def entries():
    return json.dumps(Entry.query.all(), cls=EntryEncoder)


def new_project(name):
    red = random.randint(128, 255)
    green = random.randint(128, 255)
    blue = random.randint(128, 255)
    return Project(name=name, colour_red=red, colour_green=green, colour_blue=blue)


@app.route("/add", methods=["POST"])
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


@app.route("/delete/<id>", methods=["DELETE"])
def delete(id):
    Entry.query.filter_by(id=id).delete()
    db.session.commit()


def decode_entry(dct):
    if "hour" in dct:
        return datetime(**dct)
    else:
        return dct


@app.route("/stop", methods=["post"])
def stop():
    data = json.loads(request.data, object_hook=decode_entry)
    entry = Entry.query.get(data["id"])
    entry.end = data["end"]
    db.session.commit()
    return json.dumps({"status": "ok"})


@app.route("/edit/<id>")
def edit(id):
    entry = Entry.query.get(id)
    if entry is not None:
        return render_template("edit.html", entry=entry)
    else:
        abort(404)


@app.route("/update", methods=["put"])
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


@app.route("/")
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
