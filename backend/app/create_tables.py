from sqlalchemy import inspect
from app.database import engine, Base
from app import models

def main():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n========== DATABASE TABLES ==========")
    for table in tables:
        print("CREATED:", table)

    print("\nTotal tables:", len(tables))

if __name__ == "__main__":
    main()
