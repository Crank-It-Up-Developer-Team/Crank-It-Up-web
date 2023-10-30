from functools import wraps

from flask import flash, make_response, redirect, request
import jwt
from common.db import get_db_connection
from common.mapper import Mapper


# decorator for verifying the JWT
def check_token(app, required: bool = False, adminrequired: bool = False):
    def _check_token(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            # jwt is passed in the request header
            if "token" in request.cookies:
                token = request.cookies["token"]
            # return 401 if token is not passed
            if not token:
                if required:
                    flash("You must be logged in to do that!")
                    return redirect("/login")
                else:
                    return f(None, *args, **kwargs)
            conn = get_db_connection()
            try:
                # decoding the payload to fetch the stored details
                data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
                mapper = conn.execute(
                    "SELECT * FROM mappers WHERE id = ?", (data["id"],)
                ).fetchone()
                if Mapper(mapper).islocked:
                    flash(
                        "Your account has been locked. Please contact AnnoyingRains for assistance."
                    )
                    resp = make_response(redirect("/"))
                    resp.delete_cookie("token")
                    return resp
                if adminrequired:
                    if Mapper(mapper).isadmin == False:
                        flash("Only adminstrators can access that page.")
                        return redirect("/")
            except jwt.exceptions.ExpiredSignatureError as e:
                if required:
                    flash("Your login has expired! Please log in again")
                    return redirect("/login")
                else:
                    return f(None, *args, **kwargs)
            except jwt.exceptions.PyJWTError:
                if required:
                    flash("You have an invalid token! Please log in again")
                    return redirect("/login")
                else:
                    return f(None, *args, **kwargs)
            # returns the current logged in users context to the routes
            if mapper is not None:
                # convert the mapper into an mapper object
                mapper = Mapper(mapper)
            return f(mapper, *args, **kwargs)

        return decorated

    return _check_token
