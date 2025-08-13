CREATE TABLE login(
    id serial PRIMARY KEY,
    name varchar(200)
)
CREATE TABLE shotinthedark(
    id serial PRIMARY KEY,
    name varchar(200)
)
CREATE TABLE register(
    id serial PRIMARY KEY,
    name varchar(200)
)
CREATE TABLE songs(
    id serial PRIMARY KEY,
    name varchar(200)
)
CREATE TABLE genre(
    id serial PRIMARY KEY,
    name varchar(200)
)
CREATE TABLE bands(
    id serial PRIMARY KEY,
    band_id int,
    song_id int,
    FOREIGN KEY (band_id) REFERENCES bands(id),
    FOREIGN KEY (song_id) REFERENCES songs(id))