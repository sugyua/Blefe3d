"""Autenticação e carteira de teste com PostgreSQL.

Não armazena senhas nem tokens de sessão em texto puro. Não contém
operações financeiras: todas as entradas e prêmios são créditos FICTÍCIOS.
"""
import hashlib
import os
import re
import secrets
import time
from datetime import datetime, timedelta, timezone

import psycopg
import cosmetics
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
SESSION_SECONDS = 60 * 60 * 24 * 30
GUEST_SESSION_SECONDS = 60 * 60 * 24 * 180
HASHER = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)
TEST_START_BALANCE_CENTS = 5000
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,24}$")


class AccountError(Exception):
    pass


class AuthError(AccountError):
    pass


class DatabaseUnavailable(AccountError):
    pass


def _db():
    if not DATABASE_URL:
        raise DatabaseUnavailable("O banco de contas não está configurado.")
    return psycopg.connect(DATABASE_URL, connect_timeout=6, row_factory=dict_row)


def setup():
    """Criação idempotente de tabelas para usuários e lançamentos de teste."""
    with _db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_accounts (
                  id TEXT PRIMARY KEY,
                  username TEXT NOT NULL UNIQUE,
                  password_hash TEXT NOT NULL,
                  display_name TEXT NOT NULL,
                  test_balance_cents INTEGER NOT NULL DEFAULT 5000
                    CHECK (test_balance_cents >= 0),
                  ad_free BOOLEAN NOT NULL DEFAULT FALSE,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("ALTER TABLE game_accounts ADD COLUMN IF NOT EXISTS is_guest BOOLEAN NOT NULL DEFAULT FALSE")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_guest_sessions (
                  token_hash TEXT PRIMARY KEY,
                  guest_id TEXT NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  expires_at TIMESTAMPTZ NOT NULL
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_guest_sessions_id
                ON game_guest_sessions (guest_id, expires_at)
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_sessions (
                  token_hash TEXT PRIMARY KEY,
                  account_id TEXT NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  expires_at TIMESTAMPTZ NOT NULL
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_sessions_user
                ON game_sessions (account_id, expires_at)
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_wallet_events (
                  id BIGSERIAL PRIMARY KEY,
                  event_key TEXT UNIQUE NOT NULL,
                  account_id TEXT NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                  amount_cents INTEGER NOT NULL,
                  description TEXT NOT NULL,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_wallet_events_user
                ON game_wallet_events (account_id, created_at DESC)
            """)
            # Inventário independente de saldo fictício e de dinheiro real.
            # Somente uma futura rotina administrativa validada concederá itens pagos.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_cosmetic_entitlements (
                  account_id TEXT NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                  product_id TEXT NOT NULL,
                  source TEXT NOT NULL,
                  granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  PRIMARY KEY (account_id, product_id)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS game_cosmetic_equipped (
                  account_id TEXT NOT NULL REFERENCES game_accounts(id) ON DELETE CASCADE,
                  slot TEXT NOT NULL CHECK (slot IN ('back','table','frame')),
                  product_id TEXT NOT NULL,
                  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                  PRIMARY KEY (account_id, slot)
                )
            """)


def _hash_token(token):
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _session(conn, account_id):
    token = secrets.token_urlsafe(40)
    conn.execute(
        "INSERT INTO game_sessions (token_hash,account_id,expires_at) VALUES (%s,%s,%s)",
        (_hash_token(token), account_id,
         datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS)),
    )
    return token


def _username(raw):
    name = str(raw or "").strip().lower()
    if not USERNAME_RE.fullmatch(name) or name.startswith("visitante_"):
        raise AccountError("O login deve ter entre 3 e 24 caracteres: letras, números ou _.")
    return name


def _password(raw):
    if not isinstance(raw, str) or len(raw) < 10 or len(raw) > 128:
        raise AccountError("Use uma senha de 10 a 128 caracteres.")
    return raw


def _public(row):
    if not row:
        return None
    return {"id": row["id"], "username": row["username"],
            "name": row["display_name"],
            "test_balance_cents": row["test_balance_cents"],
            "ad_free": row["ad_free"],
            "guest": bool(row.get("is_guest",False))}


def create(username, password):
    uname = _username(username)
    password = _password(password)
    pwd_hash = HASHER.hash(password)
    new_id = secrets.token_urlsafe(24)
    with _db() as conn:
        with conn.transaction():
            existing = conn.execute(
                "SELECT 1 FROM game_accounts WHERE username=%s", (uname,)
            ).fetchone()
            if existing:
                raise AccountError("Este nome de usuário já está em uso.")
            conn.execute(
                """INSERT INTO game_accounts
                   (id,username,display_name,password_hash,test_balance_cents)
                   VALUES (%s,%s,%s,%s,%s)""",
                (new_id, uname, uname, pwd_hash, TEST_START_BALANCE_CENTS),
            )
            conn.execute(
                """INSERT INTO game_wallet_events
                   (event_key,account_id,amount_cents,description)
                   VALUES (%s,%s,%s,%s)""",
                ("welcome:" + new_id, new_id, TEST_START_BALANCE_CENTS,
                 "Bônus único de boas-vindas para testes"),
            )
            token = _session(conn, new_id)
        account = find_by_id(new_id, conn)
        return account, token


def login(username, password):
    # Respostas de erro iguais em usuário inexistente e senha errada.
    try:
        uname = _username(username)
    except AccountError:
        uname = ""
    if not isinstance(password, str):
        password = ""
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM game_accounts WHERE username=%s", (uname,)
        ).fetchone()
        if not row or row.get("is_guest"):
            raise AuthError("Login ou senha incorretos.")
        try:
            HASHER.verify(row["password_hash"], password)
        except (VerifyMismatchError, VerificationError, ValueError, TypeError):
            raise AuthError("Login ou senha incorretos.")
        if HASHER.check_needs_rehash(row["password_hash"]):
            conn.execute("UPDATE game_accounts SET password_hash=%s WHERE id=%s",
                         (HASHER.hash(password), row["id"]))
        token = _session(conn, row["id"])
        return _public(row), token


def find_by_id(account_id, conn=None):
    if conn is None:
        with _db() as connection:
            return find_by_id(account_id, connection)
    return _public(conn.execute(
        "SELECT id,username,display_name,test_balance_cents,ad_free,is_guest "
        "FROM game_accounts WHERE id=%s", (account_id,)
    ).fetchone())


def from_session(token):
    if not token or len(token) > 160:
        return None
    try:
        token_hash = _hash_token(token)
    except (UnicodeEncodeError, TypeError, AttributeError):
        return None
    with _db() as conn:
        row = conn.execute(
            """SELECT a.id,a.username,a.display_name,a.test_balance_cents,a.ad_free,a.is_guest
               FROM game_accounts a
               JOIN game_sessions s ON s.account_id=a.id
               WHERE s.token_hash=%s AND s.expires_at>NOW() AND a.is_guest=FALSE""",
            (token_hash,),
        ).fetchone()
        return _public(row)


def from_guest_session(token):
    """A carteira de visitante é identificada por cookie secreto, nunca pelo IP."""
    if not token or len(token)>160:
        return None
    try:
        hashed=_hash_token(token)
    except (UnicodeEncodeError,TypeError,AttributeError):
        return None
    with _db() as conn:
        row=conn.execute(
            """SELECT a.id,a.username,a.display_name,a.test_balance_cents,a.ad_free,a.is_guest
               FROM game_accounts a JOIN game_guest_sessions s ON s.guest_id=a.id
               WHERE s.token_hash=%s AND s.expires_at>NOW() AND a.is_guest=TRUE""",
            (hashed,)
        ).fetchone()
        return _public(row)


def create_guest():
    """Cria um visitante único com R$ 50 fictícios e sessão limitada ao navegador."""
    account_id=secrets.token_urlsafe(24)
    username="visitante_"+secrets.token_hex(7)
    name="Visitante "+secrets.token_hex(2).upper()
    token=secrets.token_urlsafe(40)
    with _db() as conn:
        with conn.transaction():
            conn.execute(
                """INSERT INTO game_accounts
                   (id,username,display_name,password_hash,test_balance_cents,is_guest)
                   VALUES (%s,%s,%s,%s,%s,TRUE)""",
                (account_id,username,name,"!guest-no-password",TEST_START_BALANCE_CENTS))
            conn.execute(
                """INSERT INTO game_guest_sessions (token_hash,guest_id,expires_at)
                   VALUES (%s,%s,%s)""",
                (_hash_token(token),account_id,
                 datetime.now(timezone.utc)+timedelta(seconds=GUEST_SESSION_SECONDS)))
            conn.execute(
                """INSERT INTO game_wallet_events
                   (event_key,account_id,amount_cents,description)
                   VALUES (%s,%s,%s,%s)""",
                ("guest-welcome:"+account_id,account_id,TEST_START_BALANCE_CENTS,
                 "Bônus de teste do visitante"))
        return find_by_id(account_id,conn),token


def logout(token):
    if not token:
        return
    try:
        token_hash = _hash_token(token)
    except (UnicodeEncodeError, TypeError, AttributeError):
        return
    with _db() as conn:
        conn.execute("DELETE FROM game_sessions WHERE token_hash=%s", (token_hash,))


def history(account_id, limit=12):
    with _db() as conn:
        rows = conn.execute(
            """SELECT amount_cents,description,
                      EXTRACT(EPOCH FROM created_at)::BIGINT AS at
               FROM game_wallet_events
               WHERE account_id=%s
               ORDER BY id DESC LIMIT %s""",
            (account_id, limit),
        ).fetchall()
        return list(reversed([dict(x) for x in rows]))


def apply_events(events):
    """Executa lançamentos fictícios atomicamente.

    events: (account_id, signed_amount, description, unique_event_key).
    Replays com a mesma chave não repetem o lançamento.
    Retorna (account_id, new_balance, was_applied) por evento.
    """
    if not events:
        return []
    results = []
    with _db() as conn:
        with conn.transaction():
            for account_id, amount, description, key in events:
                # O bloqueio protege contra duas sessões debitando o mesmo saldo.
                row = conn.execute(
                    "SELECT test_balance_cents FROM game_accounts WHERE id=%s FOR UPDATE",
                    (account_id,),
                ).fetchone()
                if not row:
                    raise AccountError("Conta não encontrada.")
                prev = conn.execute(
                    "SELECT 1 FROM game_wallet_events WHERE event_key=%s", (key,)
                ).fetchone()
                if prev:
                    results.append((account_id, row["test_balance_cents"], False))
                    continue
                new_balance = row["test_balance_cents"] + amount
                if new_balance < 0:
                    raise AccountError("Saldo fictício insuficiente.")
                conn.execute(
                    "UPDATE game_accounts SET test_balance_cents=%s WHERE id=%s",
                    (new_balance, account_id),
                )
                conn.execute(
                    """INSERT INTO game_wallet_events
                       (event_key,account_id,amount_cents,description)
                       VALUES (%s,%s,%s,%s)""",
                    (key, account_id, amount, description),
                )
                results.append((account_id, new_balance, True))
        return results


def cosmetic_state(account_id):
    """Inventário e escolhas visuais persistentes, nunca derivadas do IP.

    As opções gratuitas pertencem a todas as identidades (inclusive convidados).
    Itens premium são catálogo ilustrativo, sem venda e sem acesso público ao grant.
    """
    with _db() as conn:
        if not conn.execute(
                "SELECT 1 FROM game_accounts WHERE id=%s", (account_id,)
        ).fetchone():
            raise AccountError("Conta não encontrada.")
        grants=conn.execute(
            "SELECT product_id FROM game_cosmetic_entitlements WHERE account_id=%s",
            (account_id,),
        ).fetchall()
        owned=set(cosmetics.FREE_IDS)
        for record in grants:
            if record["product_id"] in cosmetics.ITEMS:
                owned.add(record["product_id"])
        equipped=dict(cosmetics.DEFAULTS)
        rows=conn.execute(
            "SELECT slot,product_id FROM game_cosmetic_equipped WHERE account_id=%s",
            (account_id,),
        ).fetchall()
        for row in rows:
            product=cosmetics.ITEMS.get(row["product_id"])
            if (row["product_id"] in owned and
                    product and product["slot"]==row["slot"]):
                equipped[row["slot"]]=row["product_id"]
        return {"owned":sorted(owned),"equipped":equipped}


def equip_cosmetic(account_id, slot, product_id):
    """Valida a propriedade e equipa sem qualquer movimentação financeira."""
    product=cosmetics.item_for(slot,product_id)
    with _db() as conn:
        with conn.transaction():
            owner=conn.execute(
                "SELECT id FROM game_accounts WHERE id=%s FOR UPDATE",
                (account_id,),
            ).fetchone()
            if not owner:
                raise AccountError("Conta não encontrada.")
            if not product["free"]:
                granted=conn.execute(
                    """SELECT 1 FROM game_cosmetic_entitlements
                       WHERE account_id=%s AND product_id=%s""",
                    (account_id,product_id),
                ).fetchone()
                if not granted:
                    raise cosmetics.LockedCosmetic(
                        "Este item premium está disponível apenas para prévia."
                    )
            conn.execute(
                """INSERT INTO game_cosmetic_equipped
                   (account_id,slot,product_id,updated_at)
                   VALUES (%s,%s,%s,NOW())
                   ON CONFLICT (account_id,slot)
                   DO UPDATE SET product_id=EXCLUDED.product_id,
                                 updated_at=NOW()""",
                (account_id,slot,product_id),
            )
    return cosmetic_state(account_id)
