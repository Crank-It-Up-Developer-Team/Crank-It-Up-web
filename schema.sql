DROP TABLE IF EXISTS maps;
DROP TABLE IF EXISTS mappers;
DROP TABLE IF EXISTS codes;

PRAGMA user_version = 3;

CREATE TABLE mappers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    username TEXT NOT NULL,
    passhash TEXT NOT NULL,
    isadmin BOOLEAN NOT NULL,
    islocked BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE maps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    mapperid INTEGER NOT NULL,
    FOREIGN KEY (mapperid)
        REFERENCES mappers(id)
);

CREATE TABLE codes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    expired BOOLEAN NOT NULL
);