import os
import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from common.auth import check_token
from common.mapper import Mapper
from common.db import get_db_connection
from werkzeug.utils import secure_filename

bp = Blueprint("create", __name__, url_prefix="/create")


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


@bp.route("/map", methods=("GET", "POST"))
@check_token(current_app, required=True)
def map(login_mapper: Mapper):
    if request.method == "POST":
        conn = get_db_connection()
        title = request.form["title"]
        # check if the post request has the file part
        if "map-zip" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["map-zip"]
        # check to see if an empty file part is uploaded
        # as some browsers upload an empty file part when none is selected
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            if not title:
                flash("Title is required!")
                return redirect(request.url)
            else:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO maps (title, mapperid) VALUES (?, ?)",
                    (title, login_mapper.id),  # type: ignore
                )
                conn.commit()
                filename = f"{cur.lastrowid}.zip"  # type: ignore
                file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
                cur.close()
                conn.close()
                webhookURL = os.getenv("DISCORD_WEBHOOK_URL")
                print(webhookURL)
                if webhookURL is not None:
                    requests.post(
                        webhookURL,
                        json={
                            "username": login_mapper.username,
                            "embeds": [
                                {
                                    "title": title,
                                    "url": f"{current_app.config['SERVER_ADDRESS']}/{cur.lastrowid}",
                                    "description": "Uploaded a new map",
                                    "image": {
                                        "url": f"{current_app.config['SERVER_ADDRESS']}/static/maps/{filename}"
                                    },
                                }
                            ],
                        },
                    )
                return redirect(url_for("index"))
        else:
            flash(
                "You either did not attach a file, or the file extension was not allowed."
            )
            return redirect(request.url)
    else:
        conn = get_db_connection()
        conn.commit()
        conn.close()
        return render_template("create.jinja", login_mapper=login_mapper)
