import os
from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)
from common.auth import check_token
from common.mapper import Mapper
from common.db import get_db_connection
from common.db import get_map

bp = Blueprint("maps", __name__, url_prefix="/maps")


@bp.route("/<int:map_id>")
@check_token(current_app)
def map(login_mapper: Mapper, map_id):
    map = get_map(map_id)
    conn = get_db_connection()
    mapper = conn.execute(
        "SELECT username FROM mappers WHERE id = ?", (map[3],)
    ).fetchone()

    # find the next map ID depending on the previous page
    if request.args.get("via", default=None) is not None:
        referrer = request.args.get("via")
    else:
        if request.referrer:
            referrer = request.referrer.split("/")[3]
        else:
            referrer = None
    match referrer:
        case "mappers":
            nextmap = conn.execute(
                "SELECT id FROM maps WHERE mapperid = ? AND id > ? LIMIT 1",
                (map["mapperid"], map["id"]),
            ).fetchone()
            previousmap = conn.execute(
                "SELECT id FROM maps WHERE mapperid = ? AND id < ? ORDER BY id DESC LIMIT 1",
                (map["mapperid"], map["id"]),
            ).fetchone()
        case _ if referrer is not None and (
            referrer.startswith("?") or referrer == "index" or referrer == ""
        ):
            nextmap = conn.execute(
                "SELECT id FROM maps WHERE id > ? LIMIT 1",
                (map["id"],),
            ).fetchone()
            previousmap = conn.execute(
                "SELECT id FROM maps WHERE id < ? ORDER BY id DESC LIMIT 1",
                (map["id"],),
            ).fetchone()
            referrer = "index"
        case _:
            nextmap = None
            previousmap = None

    if nextmap is not None:
        nextmap = nextmap[0]

    if previousmap is not None:
        previousmap = previousmap[0]

    return render_template(
        "map.jinja",
        map=map,
        mapper=mapper[0],
        nextmap=nextmap,
        previousmap=previousmap,
        referrer=referrer,
        login_mapper=login_mapper,
    )


@bp.route("/<int:id>/edit", methods=("GET", "POST"))
@check_token(current_app, required=True)
def edit(login_mapper: Mapper, id):
    map = get_map(id)
    if request.method == "POST":
        title = request.form["title"]
        if not title:
            flash("Title is required!")
        else:
            conn = get_db_connection()
            mapperid = conn.execute(
                "SELECT mapperid FROM maps WHERE id = ?", (id,)
            ).fetchone()[0]
            if login_mapper.id == mapperid or login_mapper.isadmin:
                # all checks passed, update the database
                conn.execute(
                    "UPDATE maps SET (title) = (?, ?)" " WHERE id = ?",
                    (title, id),
                )
            else:
                flash("You can't edit other people's maps!")
            conn.commit()
            conn.close()
            return redirect(url_for("index"))
    conn = get_db_connection()
    conn.commit()
    conn.close()
    return render_template("edit.jinja", map=map, login_mapper=login_mapper)


@bp.route("/<int:id>/delete", methods=("POST",))
@check_token(current_app, required=True)
def delete(login_mapper: Mapper, id):
    map = get_map(id)
    conn = get_db_connection()
    mapperid = conn.execute("SELECT mapperid FROM maps WHERE id = ?", (id,)).fetchone()[
        0
    ]
    if login_mapper.id == mapperid or login_mapper.isadmin:
        fileext = conn.execute(
            "SELECT fileext FROM maps WHERE id = ?", (id,)
        ).fetchone()[0]
        os.remove(f"static/maps/{id}.{fileext}")
        conn.execute("DELETE FROM maps WHERE id = ?", (id,))
    else:
        flash("You can't delete other people's maps!")
        return redirect(url_for("index"))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(map["title"]))
    return redirect(url_for("index"))
