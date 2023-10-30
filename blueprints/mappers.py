from flask import Blueprint, current_app, render_template, request, make_response
from common.auth import check_token
from common.mapper import Mapper
from common.db import get_db_connection
import mimetypes

bp = Blueprint("mappers", __name__, url_prefix="/mappers")


@bp.route("/")
@check_token(current_app)
def list(login_mapper: Mapper | None):
    conn = get_db_connection()
    mappers = conn.execute("SELECT username FROM mappers").fetchall()
    conn.close()
    return render_template("mappers.jinja", mappers=mappers, login_mapper=login_mapper)


@bp.route("/<string:mapper>")
@check_token(current_app)
def mapper(login_mapper, mapper):
    conn = get_db_connection()
    page = request.args.get("page", type=int)
    if page is None:
        page = 0
    else:
        page -= 1
    offset = page * 50
    mapper_id = conn.execute(
        "SELECT id FROM mappers WHERE username = ?", (mapper,)
    ).fetchone()
    maps = conn.execute(
        "SELECT * FROM maps WHERE mapperid = ? ORDER BY created DESC LIMIT 51 OFFSET ?",
        (mapper_id[0], offset),
    ).fetchall()
    conn.close()
    # if there are more maps, allow going to the next page
    # and clean up the extra map
    if len(maps) > 50:
        maps.pop()
        allownext = True
    else:
        # if not, do not allow going to the next page
        allownext = False
    return render_template(
        "mapper.jinja",
        mapper=mapper,
        maps=maps,
        page=page + 1,
        allownext=allownext,
        login_mapper=login_mapper,
    )


@bp.route("/<string:mapper>/feed")
def feed(mapper):
    conn = get_db_connection()
    mapper_id = conn.execute(
        "SELECT id FROM mappers WHERE username = ?", (mapper,)
    ).fetchone()
    maps = conn.execute(
        "SELECT * FROM maps WHERE mapperid = ? ORDER BY created DESC",
        (mapper_id[0],),
    ).fetchall()
    mappers = conn.execute("SELECT id, username FROM mappers").fetchall()
    # convert the mapper to a dict for easy searching
    mapperdict = {}
    for other_mapper in mappers:
        mapperdict.update({other_mapper[0]: other_mapper[1]})
    conn.close()
    response = make_response(
        render_template(
            "rss/mapper.jinja",
            mapper=mapper,
            maps=maps,
            mappers=mapperdict,
            types_map=mimetypes.types_map,
        )
    )
    response.headers["Content-Type"] = "application/xml"
    return response
