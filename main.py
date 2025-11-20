from fastapi import FastAPI, HTTPException
import sqlite3
from datetime import datetime

app = FastAPI()

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
   location: str | None = None,
   species: str | None = None,
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
    query += " WHERE " + "AND ".join(conditions)

  res = cursor.execute(query, filterParams).fetchall()

  connection.close()

  return [dict(row) for row in res]

@app.get("/analytics/num_sightings/")
def getSightingsByRegion(
    interval: str,
    location: str | None = None,
    species: str | None = None,
):
  
  if interval not in ["daily", "weekly", "monthly", "yearly"]:
    raise HTTPException(status_code=422, detail="Invalid interval")  

  match interval:
    case "daily":
      strf_format = "%Y-%m-%d"
    case "weekly":
      strf_format = "%Y-%W"
    case "monthly":
      strf_format = "%Y-%m"
    case "yearly":
      strf_format = "%Y"

  query  = f"""
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
    query += " WHERE " + "AND ".join(conditions)

  query += " GROUP BY year_week ORDER BY year_week;"

  res = cursor.execute(query, filterParams).fetchall()
  connection.close()

  return [dict(row) for row in res]
