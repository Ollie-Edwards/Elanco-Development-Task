from fastapi import FastAPI
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
   latinName: str | None = None
):

  connection = create_connection()
  connection.row_factory = sqlite3.Row
  cursor = connection.cursor()
  connection.row_factory = sqlite3.Row

  baseQuery = "SELECT * FROM TickSightings"

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

  if latinName:
    conditions.append("latinName = (?)")
    filterParams.append(latinName)    

  if conditions != []:
    finalQuery = f"{baseQuery} WHERE { 'AND '.join(conditions) }"
  else:
    finalQuery = baseQuery

  res = cursor.execute(finalQuery, filterParams).fetchall()

  connection.close()

  return [dict(row) for row in res]
