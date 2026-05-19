import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base


# .env LOADER
load_dotenv()

# .env GETTER
DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:
    raise ValueError("DATABASE_URL not in .env file.")


# SQLAlchemy ENGINE
engine = create_engine(DATABASE_URL, echo=False)

# SESSION CONFIGURATION
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def init_db():


    """
    EXECUTION FLOW :

    1. Initialization of database
    2. Table creation
    3. Import of required extension (btree_gist)

    """

    with engine.connect() as conn:

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist;"))
        conn.commit()

    
    # TABLE GENERATION
    Base.metadata.create_all(bind=engine)
    print("Database schema initialized.")
    

if __name__ == "__main__":
    init_db()