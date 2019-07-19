import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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


def decode_entry(dct):
    if "hour" in dct:
        return datetime(**dct)
    else:
        return dct
