from sqlalchemy import Table, Column, DateTime, Float, Integer, PrimaryKeyConstraint, MetaData, create_engine 

# Datenbank erstellen/verbinden
engine = create_engine('sqlite:///data.db')
metadata = MetaData()

# Tabelle definieren
aggregate = Table(
    'aggregate', metadata,
    Column('timestamp', DateTime, nullable=False),
    Column('aggregate', Float, nullable=False),
    Column('user_id', Integer, nullable=False),
    PrimaryKeyConstraint('timestamp', 'user_id')
)
# Tabelle definieren
aggregate = Table(
    'seq2point', metadata,
    Column('timestamp', DateTime, nullable=False),
    Column('washingmachine', Float, nullable=False),
    Column('fridge', Float, nullable=False),
    Column('microwave', Float, nullable=False),
    Column('kettle', Float, nullable=False),
    Column('user_id', Integer, nullable=False),
    PrimaryKeyConstraint('timestamp', 'user_id')
)
# Tabelle definieren
aggregate = Table(
    'seq2seq', metadata,
    Column('timestamp', DateTime, nullable=False),
    Column('washingmachine', Float, nullable=False),
    Column('fridge', Float, nullable=False),
    Column('microwave', Float, nullable=False),
    Column('kettle', Float, nullable=False),
    Column('user_id', Integer, nullable=False),
    PrimaryKeyConstraint('timestamp', 'user_id')
)
# Tabelle definieren
aggregate = Table(
    'dae', metadata,
    Column('timestamp', DateTime, nullable=False),
    Column('washingmachine', Float, nullable=False),
    Column('fridge', Float, nullable=False),
    Column('microwave', Float, nullable=False),
    Column('kettle', Float, nullable=False),
    Column('user_id', Integer, nullable=False),
    PrimaryKeyConstraint('timestamp', 'user_id')
)

# Tabellen erstellen
metadata.create_all(engine)
