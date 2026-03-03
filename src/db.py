from __future__ import annotations

from pathlib import Path
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional, Sequence

ISO_FMT = "%Y-%m-%dT%H:%M:%S%z"
DEFAULT_DB_PATH = str(Path("data") / "doacao.db")


@dataclass(frozen=True)
class Ponto:
    id: str
    nome: str
    tipo: str  # "Ponto de arrecadação" | "Abrigo"
    bairro: str
    endereco: str
    horario: str
    contato_nome: str
    contato_whats: str
    ativo: int  # 0/1


@dataclass(frozen=True)
class Necessidade:
    id: int
    ponto_id: str
    categoria: str
    item: str
    status: str  # "URGENTE" | "PRECISA" | "OK"
    observacao: str
    updated_at: str  # ISO
    updated_by: str


def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)  # cria pasta data/ se não existir
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
    except sqlite3.OperationalError:
        # Alguns filesystems gerenciados nao suportam WAL; cai para o modo padrao.
        pass
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().strftime(ISO_FMT)


def ensure_db(db_path: str) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pontos (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                tipo TEXT NOT NULL,
                bairro TEXT NOT NULL,
                endereco TEXT NOT NULL,
                horario TEXT NOT NULL,
                contato_nome TEXT NOT NULL,
                contato_whats TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS necessidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ponto_id TEXT NOT NULL,
                categoria TEXT NOT NULL,
                item TEXT NOT NULL,
                status TEXT NOT NULL,
                observacao TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL,
                updated_by TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (ponto_id) REFERENCES pontos(id)
            );
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_necessidades_ponto
            ON necessidades(ponto_id);
            """
        )

        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_necessidades_cat_status
            ON necessidades(categoria, status);
            """
        )

        conn.commit()
    finally:
        conn.close()


def resolve_db_path(db_path: Optional[str] = None) -> str:
    return db_path or DEFAULT_DB_PATH


def seed_if_empty(db_path: str) -> None:
    """Cria alguns pontos/itens de exemplo só se o banco estiver vazio."""
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM pontos;")
        n = int(cur.fetchone()["n"])
        if n > 0:
            return

        pontos = [
            ("ponto_centro_1", "Ponto Centro (Exemplo)", "Ponto de arrecadação", "Centro", "Av. Exemplo, 123", "09:00–18:00", "Equipe", "32999990000", 1),
            ("abrigo_norte_1", "Abrigo Zona Norte (Exemplo)", "Abrigo", "Zona Norte", "Rua Exemplo, 45", "08:00–20:00", "Coordenação", "32988880000", 1),
        ]
        cur.executemany(
            """
            INSERT INTO pontos (id, nome, tipo, bairro, endereco, horario, contato_nome, contato_whats, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            pontos,
        )

        itens = [
            ("ponto_centro_1", "Água", "Água mineral 1,5L", "URGENTE", "", now_iso(), "seed"),
            ("ponto_centro_1", "Higiene", "Sabonete", "PRECISA", "", now_iso(), "seed"),
            ("ponto_centro_1", "Roupas", "Roupas adultas", "OK", "Somente em bom estado", now_iso(), "seed"),
            ("abrigo_norte_1", "Limpeza", "Água sanitária", "URGENTE", "", now_iso(), "seed"),
            ("abrigo_norte_1", "Fraldas", "Fralda G", "PRECISA", "", now_iso(), "seed"),
        ]
        cur.executemany(
            """
            INSERT INTO necessidades (ponto_id, categoria, item, status, observacao, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            itens,
        )

        conn.commit()
    finally:
        conn.close()


def list_pontos(db_path: str, only_active: bool = True) -> list[Ponto]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        if only_active:
            cur.execute("SELECT * FROM pontos WHERE ativo=1 ORDER BY bairro, nome;")
        else:
            cur.execute("SELECT * FROM pontos ORDER BY ativo DESC, bairro, nome;")
        rows = cur.fetchall()
        return [Ponto(**dict(r)) for r in rows]
    finally:
        conn.close()


def get_ponto(db_path: str, ponto_id: str) -> Optional[Ponto]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM pontos WHERE id=?;", (ponto_id,))
        row = cur.fetchone()
        return Ponto(**dict(row)) if row else None
    finally:
        conn.close()


def upsert_ponto(db_path: str, ponto: Ponto) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO pontos (id, nome, tipo, bairro, endereco, horario, contato_nome, contato_whats, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome=excluded.nome,
                tipo=excluded.tipo,
                bairro=excluded.bairro,
                endereco=excluded.endereco,
                horario=excluded.horario,
                contato_nome=excluded.contato_nome,
                contato_whats=excluded.contato_whats,
                ativo=excluded.ativo;
            """,
            (
                ponto.id,
                ponto.nome,
                ponto.tipo,
                ponto.bairro,
                ponto.endereco,
                ponto.horario,
                ponto.contato_nome,
                ponto.contato_whats,
                ponto.ativo,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def insert_ponto_if_missing(db_path: str, ponto: Ponto) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO pontos
            (id, nome, tipo, bairro, endereco, horario, contato_nome, contato_whats, ativo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                ponto.id,
                ponto.nome,
                ponto.tipo,
                ponto.bairro,
                ponto.endereco,
                ponto.horario,
                ponto.contato_nome,
                ponto.contato_whats,
                ponto.ativo,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def list_existing_ponto_ids(db_path: str, ponto_ids: Sequence[str]) -> set[str]:
    if not ponto_ids:
        return set()

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT id FROM pontos
            WHERE id IN ({",".join(["?"] * len(ponto_ids))});
            """,
            tuple(ponto_ids),
        )
        return {str(row["id"]) for row in cur.fetchall()}
    finally:
        conn.close()


def list_necessidades(
    db_path: str,
    ponto_ids: Optional[Sequence[str]] = None,
    categoria: Optional[str] = None,
    status: Optional[str] = None,
) -> list[Necessidade]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()

        where = []
        params: list[object] = []

        if ponto_ids:
            where.append(f"ponto_id IN ({','.join(['?'] * len(ponto_ids))})")
            params.extend(list(ponto_ids))
        if categoria and categoria != "Todas":
            where.append("categoria = ?")
            params.append(categoria)
        if status and status != "Todos":
            where.append("status = ?")
            params.append(status)

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        cur.execute(
            f"""
            SELECT * FROM necessidades
            {where_sql}
            ORDER BY updated_at DESC;
            """,
            tuple(params),
        )
        rows = cur.fetchall()
        return [Necessidade(**dict(r)) for r in rows]
    finally:
        conn.close()


def last_update_for_ponto(db_path: str, ponto_id: str) -> Optional[str]:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT MAX(updated_at) AS last_upd
            FROM necessidades
            WHERE ponto_id=?;
            """,
            (ponto_id,),
        )
        row = cur.fetchone()
        return row["last_upd"] if row and row["last_upd"] else None
    finally:
        conn.close()


def add_necessidade(
    db_path: str,
    ponto_id: str,
    categoria: str,
    item: str,
    status: str,
    observacao: str,
    updated_by: str,
) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO necessidades (ponto_id, categoria, item, status, observacao, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (ponto_id, categoria, item, status, observacao or "", now_iso(), updated_by or ""),
        )
        conn.commit()
    finally:
        conn.close()


def set_ponto_ativo(db_path: str, ponto_id: str, ativo: bool) -> None:
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("UPDATE pontos SET ativo=? WHERE id=?;", (1 if ativo else 0, ponto_id))
        conn.commit()
    finally:
        conn.close()
