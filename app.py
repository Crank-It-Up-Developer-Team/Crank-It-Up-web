from flask import (
    Flask,
    render_template,
    request,
    redirect,
    make_response,
)
import os
from dotenv import load_dotenv
from flask_sitemap import Sitemap
from common.auth import check_token
from common.mapper import Mapper
import upgrade_db
import mimetypes
import subprocess
from common.db import get_db_connection

import blueprints.admin
import blueprints.mappers
import blueprints.auth
import blueprints.maps
import blueprints.create


upgrade_db.upgrade_if_needed()

load_dotenv()

SITEMAP_URLS = (
    "index",
    "auth.login",
    "mappers.list",
    "rss",
    "auth.create_account",
)


maxlogintime = os.getenv("MAX_LOGIN_TIME")
if maxlogintime is not None:
    if not maxlogintime.isnumeric():
        print("invalid config!")
        exit()
else:
    print("invalid config!")
    exit()
if os.getenv("SECRET_KEY") is None:
    print("invalid config!")
    exit()

if os.getenv("SERVER_ADDRESS") is None:
    print("invalid config!")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["UPLOAD_FOLDER"] = "static/maps"
app.config["MAX_LOGIN_TIME"] = int(maxlogintime)
app.config["ALLOWED_EXTENSIONS"] = "zip"
app.config["SERVER_ADDRESS"] = os.getenv("SERVER_ADDRESS")
ext = Sitemap(app=app)


@app.context_processor
def inject_version_info():
    return dict(
        COMMIT_ID=subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"]
        ).decode(),
        VERSION=subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"]
        ).decode(),
    )


app.register_blueprint(blueprints.admin.bp)
app.register_blueprint(blueprints.mappers.bp)
app.register_blueprint(blueprints.auth.bp)
app.register_blueprint(blueprints.maps.bp)
app.register_blueprint(blueprints.create.bp)


@app.route("/")
@check_token(app)
def index(login_mapper: Mapper | None):
    conn = get_db_connection()
    page = request.args.get("page", type=int)
    if page is None:
        page = 0
    else:
        page -= 1
    # pages are 50 items long
    offset = page * 50
    # request one more map than we need, purely to see if it exists
    maps = conn.execute(
        "SELECT * FROM maps ORDER BY created DESC LIMIT 51 OFFSET ?",
        (offset,),
    ).fetchall()
    # if there are more maps, allow going to the next page
    # and clean up the extra map
    if len(maps) > 50:
        maps.pop()
        allownext = True
    else:
        # if not, do not allow going to the next page
        allownext = False
    mappers = conn.execute("SELECT id, username FROM mappers").fetchall()
    # convert the mapper to a dict for easy searching
    mapperdict = {}
    for other_mapper in mappers:
        mapperdict.update({other_mapper[0]: other_mapper[1]})
    conn.close()
    return render_template(
        "index.jinja",
        maps=maps,
        mappers=mapperdict,
        page=page + 1,
        allownext=allownext,
        login_mapper=login_mapper,
    )


@app.route("/feed")
def indexrssfeed():
    conn = get_db_connection()
    maps = conn.execute("SELECT * FROM maps ORDER BY created DESC").fetchall()
    mappers = conn.execute("SELECT id, username FROM mappers").fetchall()
    # convert the mapper to a dict for easy searching
    mapperdict = {}
    for other_mapper in mappers:
        mapperdict.update({other_mapper[0]: other_mapper[1]})
    conn.close()
    response = make_response(
        render_template(
            "rss/index.jinja",
            maps=maps,
            mappers=mapperdict,
            types_map=mimetypes.types_map,
        )
    )
    response.headers["Content-Type"] = "application/xml"
    return response


@app.route("/rss")
@check_token(app)
def rss(login_mapper: Mapper):
    return render_template("rss.jinja", login_mapper=login_mapper)


@app.route("/toggletheme")
def toggletheme():
    if request.referrer is not None:
        resp = make_response(redirect(request.referrer))
    else:
        resp = make_response(redirect("/"))
    if request.cookies.get("darkmode", default=None) is None:
        resp.set_cookie("darkmode", "true")
    else:
        resp.delete_cookie("darkmode")
    return resp


@ext.register_generator
def sitemap():
    for page in SITEMAP_URLS:
        yield page, {}
    conn = get_db_connection()
    maps = conn.execute("SELECT id FROM maps ORDER BY created DESC").fetchall()
    for map in maps:
        yield "maps.map", {"map_id": map[0]}
    mappers = conn.execute(
        "SELECT username FROM mappers ORDER BY created DESC"
    ).fetchall()
    for mapper in mappers:
        yield "mappers.mapper", {"mapper": mapper[0]}
