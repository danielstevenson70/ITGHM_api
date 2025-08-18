CREATE TABLE IF NOT EXISTS genre (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name text NOT NULL
);

INSERT INTO bands(band_name)
    VALUES('The Acaica Strain'),
    ('Bad Omens'),
    ('Between The Buried and Me'),
    ('Meshuggah');

INSERT INTO genre (name)
    VALUES ('Deathcore'),
    ('Metalcore'),
    ('Progressive Metal')
    ('Death Metal');
    

