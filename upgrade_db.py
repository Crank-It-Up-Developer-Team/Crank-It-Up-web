import sqlite3


def upgrade_if_needed():
    connection = sqlite3.connect("db/database.db")
    version: int = connection.execute("SELECT * FROM pragma_user_version").fetchone()[0]
    # if version < REPLACEME:
    #    print(f"upgrading from v{version} to vREPLACEME!")
    #    connection.execute(
    #        "REPLACEME"
    #    )
    #    connection.execute("PRAGMA user_version = REPLACEME")
    # connection.commit()
    # connection.close()


if __name__ == "__main__":
    upgrade_if_needed()
