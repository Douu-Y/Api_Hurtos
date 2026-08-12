from fastapi import FastAPI, HTTPException
from database import crear_tablas, get_connection
from models import Hurto, TipoHurto
from psycopg import errors

app = FastAPI()

crear_tablas()

# ------------------------------------------------------------------

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la API de Hurtos"}


@app.post("/tipos-hurto")
def crear_tipo_hurto(tipo: TipoHurto):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT idtipo FROM tipo_hurto WHERE nombre = %s", (tipo.nombre,))
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="El tipo de hurto ya existe")

    cur.execute(
        "INSERT INTO tipo_hurto (nombre) VALUES (%s) RETURNING idtipo",
        (tipo.nombre,)
    )
    nuevo_id = cur.fetchone()["idtipo"]
    conn.commit()
    cur.close()
    conn.close()
    return {"mensaje": "Tipo de hurto creado", "idtipo": nuevo_id}


@app.get("/tipos-hurto")
def obtener_tipos_hurto():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT idtipo, nombre FROM tipo_hurto ORDER BY idtipo")
    tipos = cur.fetchall()
    cur.close()
    conn.close()
    return {"tipos_hurto": tipos}


@app.get("/tipos-hurto/{idtipo}")
def obtener_tipo_hurto(idtipo: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT idtipo, nombre FROM tipo_hurto WHERE idtipo = %s", (idtipo,))
    tipo = cur.fetchone()
    cur.close()
    conn.close()

    if tipo is None:
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")
    return tipo


@app.get("/tipos-hurto/{idtipo}/hurtos")
def obtener_hurtos_por_tipo(idtipo: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT idtipo FROM tipo_hurto WHERE idtipo = %s", (idtipo,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")

    cur.execute(
        "SELECT id, denunciante, direccion, fechahurto, fecharegistro FROM hurto WHERE idtipohurto = %s ORDER BY id",
        (idtipo,)
    )
    hurtos = cur.fetchall()
    cur.close()
    conn.close()
    return {"hurtos": hurtos}


@app.delete("/tipos-hurto/{idtipo}")
def eliminar_tipo_hurto(idtipo: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT idtipo FROM tipo_hurto WHERE idtipo = %s", (idtipo,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Tipo de hurto no encontrado")

    try:
        cur.execute("DELETE FROM tipo_hurto WHERE idtipo = %s", (idtipo,))
        conn.commit()
    except errors.RestrictViolation:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el tipo de hurto porque tiene hurtos asociados"
        )

    cur.close()
    conn.close()
    return {"mensaje": "Tipo de hurto eliminado"}


# endpoints de hurto

@app.post("/hurtos")
def crear_hurto(hurto: Hurto):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT idtipo, nombre FROM tipo_hurto WHERE idtipo = %s", (hurto.idtipohurto,))
    tipo = cur.fetchone()
    if not tipo:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="El tipo de hurto no existe")

    cur.execute(
        "INSERT INTO hurto (idtipohurto, denunciante, direccion, fechahurto) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (hurto.idtipohurto, hurto.denunciante, hurto.direccion, hurto.fechahurto)
    )
    nuevo_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {
        "mensaje": "Hurto registrado",
        "id": nuevo_id,
        "tipo_hurto": tipo["nombre"]
    }


@app.get("/hurtos")
def obtener_hurtos():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
    "SELECT hurto.id, hurto.idtipohurto, tipo_hurto.nombre AS tipo_hurto, "
    "hurto.denunciante, hurto.direccion, hurto.fechahurto, hurto.fecharegistro "
    "FROM hurto "
    "JOIN tipo_hurto ON hurto.idtipohurto = tipo_hurto.idtipo "
    "ORDER BY hurto.id"
    )
    hurtos = cur.fetchall()
    cur.close()
    conn.close()
    return {"hurtos": hurtos}


@app.get("/hurtos/{id}")
def obtener_hurto(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
    "SELECT hurto.id, hurto.idtipohurto, tipo_hurto.nombre AS tipo_hurto, "
    "hurto.denunciante, hurto.direccion, hurto.fechahurto, hurto.fecharegistro "
    "FROM hurto "
    "JOIN tipo_hurto ON hurto.idtipohurto = tipo_hurto.idtipo "
    "WHERE hurto.id = %s",
    (id,)
    )
    hurto = cur.fetchone()
    cur.close()
    conn.close()

    if hurto is None:
        raise HTTPException(status_code=404, detail="Hurto no encontrado")
    return hurto


@app.put("/hurtos/{id}")
def actualizar_hurto(id: int, hurto: Hurto):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT idtipo, nombre FROM tipo_hurto WHERE idtipo = %s", (hurto.idtipohurto,))
    tipo = cur.fetchone()
    if not tipo:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="El tipo de hurto no existe")

    cur.execute(
        "UPDATE hurto SET idtipohurto = %s, denunciante = %s, direccion = %s, fechahurto = %s WHERE id = %s",
        (hurto.idtipohurto, hurto.denunciante, hurto.direccion, hurto.fechahurto, id)
    )
    affect_rows = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if affect_rows == 0:
        raise HTTPException(status_code=404, detail="Hurto no encontrado")
    return {
        "mensaje": "Hurto actualizado",
        "tipo_hurto": tipo["nombre"]
    }


@app.delete("/hurtos/{id}")
def eliminar_hurto(id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT h.id, t.nombre AS tipo_hurto "
        "FROM hurto h JOIN tipo_hurto t ON h.idtipohurto = t.idtipo "
        "WHERE h.id = %s",
        (id,)
    )
    hurto = cur.fetchone()
    if not hurto:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Hurto no encontrado")

    cur.execute("DELETE FROM hurto WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return {
        "mensaje": "Hurto eliminado",
        "tipo_hurto": hurto["tipo_hurto"]
    }