from fastapi import FastAPI, HTTPException, Query
import sqlite3
from datetime import datetime
from enum import Enum
import datetime as dt
from contextlib import asynccontextmanager
import os
import pandas as pd

DB_PATH = "tickSightings.db"
DATA_PATH = "tickSightings.xlsx"


class LocationEnum(str, Enum):
    Birmingham = "Birmingham"
    Bristol = "Bristol"
    Cardiff = "Cardiff"
    Edinburgh = "Edinburgh"
    Glasgow = "Glasgow"
    Leeds = "Leeds"
    Leicester = "Leicester"
    Liverpool = "Liverpool"
    London = "London"
    Manchester = "Manchester"
    Newcastle = "Newcastle"
    Nottingham = "Nottingham"
    Sheffield = "Sheffield"
    Southampton = "Southampton"


class SpeciesEnum(str, Enum):
    FoxBadger = "Fox/badger tick"
    Marsh = "Marsh tick"
    Passerine = "Passerine tick"
    SouthernRodent = "Southern rodent tick"
    TreeHole = "Tree-hole tick"


class IntervalEnum(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class LatinNameEnum(str, Enum):
    IxodesApronophorus = "Ixodes apronophorus"
    IxodesAcuminatus = "Ixodes acuminatus"
    DermacentorFrontalis = "Dermacentor frontalis"
    IxodesArboricola = "Ixodes arboricola"
    IxodesCanisuga = "Ixodes canisuga"


latinNameDictionary = {
    "Passerine tick": "Dermacentor frontalis",
    "Southern rodent tick": "Ixodes acuminatus",
    "Tree-hole tick": "Ixodes arboricola",
    "Fox/badger tick": "Ixodes canisuga",
    "Marsh tick": "Ixodes apronophorus",
}

def connectToDB():
    try:
        connection = sqlite3.connect(DB_PATH)
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error - Database failed to connect."
        )
    return connection

def CreateDB():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS TickSightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME NOT NULL,
            location TEXT NOT NULL,
            species TEXT NOT NULL,
            latinName TEXT NOT NULL,

            UNIQUE(date, location, species, latinName)
        );
        """
    )
    conn.commit()
    conn.close()

    print("DB successfully created")


def loadData():
    if not os.path.exists(DATA_PATH):
        print("Spreadsheet not found, DB is empty")
        return

    print("Spreadsheet found, importing data")

    try:
        df = pd.read_excel(DATA_PATH, engine="openpyxl")
    except Exception as e:
        print("Error reading spreadsheet:", e)
        return

    # Ensure that location, species and latin name match the required enums, remove entires with non valid locations and species
    locations = set([item.value for item in LocationEnum])
    species = set([item.value for item in SpeciesEnum])
    latinName = set([item.value for item in LatinNameEnum])

    df = df[df["location"].isin(locations)]
    df = df[df["species"].isin(species)]
    df = df[df["latinName"].isin(latinName)]

    # Remove rows with missing values
    requiredCols = ["date", "location", "species", "latinName"]
    df = df[requiredCols]
    df = df.dropna()

    # Ensure provided dates are valid, remove any rows with invalid dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Remove unreasonable dates (more than 50 years ago, and in the future)
    today = pd.Timestamp.today()
    fifty_years_ago = today - pd.DateOffset(years=50)
    df = df[(df["date"] >= fifty_years_ago) & (df["date"] <= today)]

    # Convert to ISO string
    df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Remove duplicates from the dataset
    df = df.drop_duplicates(subset=["date", "location", "species", "latinName"])

    # Convert dataframe to list of tuples
    data_tuples = list(
        df[["date", "location", "species", "latinName"]].itertuples(
            index=False, name=None
        )
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executemany(
        """
        INSERT INTO TickSightings (date, location, species, latinName)
        VALUES (?, ?, ?, ?)
        """,
        data_tuples,
    )

    conn.commit()
    conn.close()
    print(f"Imported {len(data_tuples)} rows from spreadsheet.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")

    if not os.path.exists(DB_PATH):
        print("DB not found, Creating DB")
        CreateDB()
        loadData()

    else:
        print("DB exists. Skipping data load")

    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)


@app.get("/sightings")
def getSightings(
    startDate: datetime | None = None,
    endDate: datetime | None = None,
    location: LocationEnum | None = None,
    species: SpeciesEnum | None = None,
    limit: int = Query(default=10, le=500),
):

    connection = connectToDB()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    query = "SELECT * FROM TickSightings"

    conditions = []
    filterParams = []

    if startDate:
        conditions.append("DATETIME(date) >= (?)")
        filterParams.append(startDate)

    if endDate:
        conditions.append("DATETIME(date) <= (?)")
        filterParams.append(endDate)

    if location:
        conditions.append("location = (?)")
        filterParams.append(location)

    if species:
        conditions.append("species = (?)")
        filterParams.append(species)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " LIMIT (?)"
    filterParams.append(str(limit))

    res = cursor.execute(query, filterParams).fetchall()
    connection.close()

    return [dict(row) for row in res]


@app.get("/analytics/num_sightings_by_interval")
def getSightingsByInterval(
    interval: IntervalEnum,
    location: LocationEnum | None = None,
    species: SpeciesEnum | None = None,
):

    match interval:
        case "daily":
            strf_format = "%Y-%m-%d"
        case "weekly":
            strf_format = "%Y-%W"
        case "monthly":
            strf_format = "%Y-%m"
        case "yearly":
            strf_format = "%Y"

    query = f"""
    SELECT 
      strftime(?, date) AS year_week,
      COUNT(*) AS num_sightings
    FROM TickSightings
  """

    conditions = []
    filterParams = [strf_format]

    if location:
        conditions.append("location = (?)")
        filterParams.append(location)

    if species:
        conditions.append("species = (?)")
        filterParams.append(species)

    connection = connectToDB()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY year_week ORDER BY year_week;"

    res = cursor.execute(query, filterParams).fetchall()
    connection.close()

    return [dict(row) for row in res]


@app.get("/analytics/num_sightings_per_region/")
def getSightingsPerRegion():
    connection = connectToDB()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    res = cursor.execute(
        """
        SELECT location, COUNT(*) as count
        FROM TickSightings
        GROUP BY location
    """
    ).fetchall()

    return [dict(row) for row in res]


@app.post("/sighting")
def addSighting(
    location: LocationEnum,
    species: SpeciesEnum,
    latinName: LatinNameEnum,
    date: datetime | None = None,
):
    now = dt.datetime.now()

    if date is None:
        date = now

    else:
        if date > now:
            raise HTTPException(
                status_code=400,
                detail="Invalid Date - Date cannot be in the future."
            )

        fiftyYearsAgo = now - dt.timedelta(days=50*365)
        if date < fiftyYearsAgo:
            raise HTTPException(
                status_code=400,
                detail="Invalid Date - Date cannot be more than 50 years ago"
            )
        

    if latinName != latinNameDictionary[species]:
        raise HTTPException(
            status_code=409, detail="Conflict: species and latin name do not match"
        )

    connection = connectToDB()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    res = cursor.execute(
        """
            INSERT INTO TickSightings (date, location, species, latinName)
            VALUES (?, ?, ?, ?) 
        """,
        [date, location, species, latinName],
    )

    return {"message": "Success"}
