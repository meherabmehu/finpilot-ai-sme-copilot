"""Provision only a new disposable DB on an explicitly selected local test cluster."""
from contextlib import contextmanager
import getpass
import os
import uuid


@contextmanager
def isolated_database(socket=None, port=55433):
    if socket is None:
        os.environ.pop('FINPILOT_EVAL_DB_NAME', None)
        yield 'disposable in-memory SQLite'
        return
    socket = socket.resolve()
    if not socket.is_dir() or not (socket / 'FINPILOT-ISOLATED-CLUSTER').is_file():
        raise ValueError('PostgreSQL requires a local socket directory marked FINPILOT-ISOLATED-CLUSTER')
    import psycopg
    from psycopg import sql
    name = 'test_finpilot_agentic_' + uuid.uuid4().hex
    # Windows PostgreSQL has no Unix-domain sockets. Pin loopback and verify
    # the server's data directory against the explicitly marked local cluster.
    host = '127.0.0.1' if os.name == 'nt' else str(socket)
    options = {'host': host, 'port': port, 'user': getpass.getuser(), 'dbname': 'postgres', 'connect_timeout': 5}
    admin = psycopg.connect(**options, autocommit=True)
    if os.name == 'nt':
        from pathlib import Path
        if Path(admin.execute('SHOW data_directory').fetchone()[0]).resolve() != socket:
            admin.close()
            raise ValueError('Loopback server does not match the explicitly marked disposable cluster')
    try:
        admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C'").format(sql.Identifier(name)))
        os.environ.update(FINPILOT_EVAL_DB_NAME=name, FINPILOT_EVAL_DB_SOCKET=host, FINPILOT_EVAL_DB_PORT=str(port))
        yield 'disposable local PostgreSQL database; ' + name
    finally:
        # No existing database is ever dropped; name is generated here, never read from input.
        from django.db import connections
        connections.close_all()
        admin.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()
        for key in ('FINPILOT_EVAL_DB_NAME', 'FINPILOT_EVAL_DB_SOCKET', 'FINPILOT_EVAL_DB_PORT'):
            os.environ.pop(key, None)
