import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE")

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

# -------------------------------------------------------------------
# Api_Hurtos

def crear_tablas():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tipo_hurto(
        idtipo SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE
        )
        """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS hurto(
    id SERIAL PRIMARY KEY,
    idtipohurto INTEGER NOT NULL,
    denunciante VARCHAR(150) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    fechahurto DATE NOT NULL,
    fecharegistro TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_tipohurto
        FOREIGN KEY (idtipohurto)
        REFERENCES tipo_hurto(idtipo)
        ON DELETE RESTRICT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()