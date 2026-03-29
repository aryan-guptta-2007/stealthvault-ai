from sqlalchemy import create_engine, select, text
from app.config import settings

def check_db():
    engine = create_engine(settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"))
    with engine.connect() as conn:
        print("--- TENANTS ---")
        tenants = conn.execute(text("SELECT * FROM tenants")).fetchall()
        for t in tenants:
            print(t)
        
        print("\n--- USERS ---")
        users = conn.execute(text("SELECT * FROM users")).fetchall()
        for u in users:
            print(u)

if __name__ == "__main__":
    check_db()
