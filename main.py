from fastapi import FastAPI, HTTPException
import sqlite3
from datetime import datetime
from enum import Enum
import datetime as dt
from contextlib import asynccontextmanager

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    # Startup logic here
    yield
    print("Shutting down...")
    # Cleanup logic here


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
    "Southern rodent tick" : "Ixodes acuminatus",
    "Tree-hole tick" : "Ixodes arboricola",
    "Fox/badger tick" : "Ixodes canisuga",
    "Marsh tick" : "Ixodes apronophorus",
}

def create_connection():
    connection = sqlite3.connect("database.db")
    return connection


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/sightings")
def getSightings(
    startDate: datetime | None = None,
    endDate: datetime | None = None,
    location: LocationEnum | None = None,
    species: SpeciesEnum | None = None,
):

    connection = create_connection()
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

    res = cursor.execute(query, filterParams).fetchall()

    connection.close()

    return [dict(row) for row in res]


@app.get("/analytics/num_sightings_by_interval")
def getSightingsByInInterval(
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

    connection = create_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " GROUP BY year_week ORDER BY year_week;"

    res = cursor.execute(query, filterParams).fetchall()
    connection.close()

    return [dict(row) for row in res]


@app.get("/analytics/num_sightings_per_region/")
def getSightingsByInInterval():
    connection = create_connection()
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
def getSightingsByInInterval(
    location: LocationEnum,
    species: SpeciesEnum,
    latinName: LatinNameEnum,
    date: datetime | None = dt.datetime.now(),
):
  
  if latinName != latinNameDictionary[species]:
    raise HTTPException(status_code=409, detail="Conflict: species and latin name do not match")
    
  connection = create_connection()
  connection.row_factory = sqlite3.Row
  cursor = connection.cursor()

  res = cursor.execute(
      """
  INSERT INTO TickSightings (id, date, location, species, latinName)
  VALUES (?, ?, ?, ?, ?) 
  """, ["id", date, location, species, latinName]) 

