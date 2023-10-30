import os
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
from werkzeug.security import generate_password_hash

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@check_token(current_app, required=True, adminrequired=True)
def admin(login_mapper):
    return render_template("admin_panel.jinja", login_mapper=login_mapper)


@bp.route("/create_signup_code", methods=("POST",))
@check_token(current_app, required=True, adminrequired=True)
def create_signup_code(login_mapper: Mapper):
    conn = get_db_connection()
    code = request.form["code"]
    conn.execute("INSERT INTO codes (code, expired) VALUES (?, ?)", (code, False))
    conn.commit()
    conn.close()
    flash(f'Signup code "{code}" was successfully created!')
    return redirect(url_for("admin.admin"))


@bp.route("/create_mapper", methods=("POST",))
@check_token(current_app, required=True, adminrequired=True)
def create_mapper(login_mapper: Mapper):
    conn = get_db_connection()
    username = request.form["username"]
    passhash = generate_password_hash(request.form["password"])
    try:
        isadmin = request.form["isadmin"]
    except:
        isadmin = False
    conn.execute(
        "INSERT INTO mappers (username, passhash, isadmin) VALUES (?, ?, ?)",
        (username, passhash, isadmin),
    )
    conn.commit()
    conn.close()
    flash(f'mapper "{username}" was successfully created!')
    return redirect(url_for("admin.admin"))


@bp.route("/lock_mapper", methods=("POST",))
@check_token(current_app, required=True, adminrequired=True)
def lock_mapper(login_mapper: Mapper):
    conn = get_db_connection()
    username = request.form["username"]
    conn.execute(
        "UPDATE mappers SET islocked = 1 WHERE username = ?",
        (username,),
    )
    conn.commit()
    conn.close()
    flash(f'mapper "{username}" was successfully locked!')
    return redirect(url_for("admin.admin"))


@bp.route("/unlock_mapper", methods=("POST",))
@check_token(current_app, required=True, adminrequired=True)
def unlock_mapper(login_mapper: Mapper):
    conn = get_db_connection()
    username = request.form["username"]
    conn.execute(
        "UPDATE mappers SET islocked = 0 WHERE username = ?",
        (username,),
    )
    conn.commit()
    conn.close()
    flash(f'mapper "{username}" was successfully unlocked!')
    return redirect(url_for("admin.admin"))


@bp.route("/delete_mapper", methods=("POST",))
@check_token(current_app, required=True, adminrequired=True)
def delete_mapper(login_mapper: Mapper):
    conn = get_db_connection()
    username = request.form["username"]
    mapperid = conn.execute(
        "SELECT id FROM mappers WHERE username = ?", (username,)
    ).fetchone()[0]
    maps = conn.execute(
        "SELECT id, fileext FROM maps WHERE mapperid = ?",
        (mapperid,),
    ).fetchall()
    for map in maps:
        try:
            os.remove(f"static/maps/{map[0]}.{map[1]}")
        except Exception as e:
            flash(str(e))

    conn.execute(
        "DELETE FROM maps WHERE mapperid = ?",
        (mapperid,),
    )
    conn.execute(
        "DELETE FROM mappers WHERE id = ?",
        (mapperid,),
    )
    conn.commit()
    conn.close()
    flash(f'mapper "{username}" was successfully deleted.')
    return redirect(url_for("admin.admin"))
