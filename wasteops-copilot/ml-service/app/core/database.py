"""Read-only inference database engine construction."""

from sqlalchemy import create_engine, event


def create_read_only_engine(url: str):
    if not url:
        return None
    engine = create_engine(url, pool_pre_ping=True)

    @event.listens_for(engine, "connect")
    def _read_only(dbapi_connection, _record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY")
        finally:
            cursor.close()

    return engine
