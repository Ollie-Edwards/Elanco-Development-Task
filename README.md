## Instructions for running the project 

* Clone Git Repository

```
git clone https://github.com/Ollie-Edwards/Elanco-Development-Task.git
```

* cd into project folder

```
cd Elanco-Development-Task
```

* Install required python libraries

```
pip install -r requirements.txt
```

* Run API using uvicorn

```
uvicorn main:app --reload
```

## Project architecture and technologies

For this project I used FastAPI which is a Python based web framework for building APIs. I paired this with Pandas for dealing with large datasets efficiently, and SQLite for managing complex queries efficiently.
Postman was used extensively to test the API ensuring that all endpoints produced the expected outputs.

### The backend is composed of 4 main endpoints:

* ` GET /sightings `
  ```
  startDate: datetime (optional),
  endDate: datetime (optional),
  location: string (optional),
  species: string (optional),
  limit: integer (optional, default=50),
  ```
  Returns tick sighting records, optionally filtered by start and end date, location, or species, with a limit on the number of results returned (default = 50).

* ` POST /sighting `
  ```
  location: string,
  species: string,
  latinName: string,
  date: datetime (optional),
  ```

  Adds a new tick sighting record with a specified location, species, and Latin name. The date defaults to the current time if not provided.

* ` GET /analytics/num_sightings_per_region `
  ```
  location: string,
  species: string,
  latinName: string,
  date: datetime (optional),
  ```
  Returns the total number of tick sightings for each region.

* `GET /analytics/num_sightings_by_interval`
  ```
  interval: ["daily", "weekly", "monthly", "yearly"],
  location: string (optional),
  species: string (optional),
  ```
  Returns the number of tick sightings grouped by a specified time interval (daily, weekly, monthly, or yearly). Optionally, the results can be filtered by location and/or species.
  This endpoint can be used to see trends over time.

## How the system consumes and presents data

When the project is first loaded, it checks if a database currently exists in the project folder. If there is no database in the project folder it automatically creates a database and then checks for an Excel file (like the one provided with the challenge) which can be used to import existing tick sightings.

If an Excel file is found, each row of data is checked to ensure:
* All records are complete and contain date, location, species and latinName fields, and any extra fields are ignored
* Location, Species, and latinName are all allowed values
* The provided dates are valid date types, and are reasonable (not in the future or too far in the past)
* No two records can be duplicates

Any records which do not fit this critera are ignored, while the remaining records are added to the database.
All records are processed and verified in a pandas dataframe, before being added to the SQLite database all at once, as this greatly improves performance on large datasets compared to fetching, verifying and adding each record one by one.

When adding new data to the database with the POST /sighting, before being added to the database, the data is checked to ensure it is unique (using the unique constraint on the database), that all attributes are included and valid, that the provided datetime object is valid, and that the specified species
name matches the provided latinName.

## Error Handling

The aim of error handling in this application is to validate user input and check for API errors, and return these errors gracefully to the user, preventing API failiures, crashes, or allowing data inconsistency. 

### Input validation

All user input is validated using date ranges and enums, if validations fail then the API returns clear HTTP errors. 400 Bad Request for invalid dates, 409 Conflict for mismatched species and latin name, and 422 Unprocessable Entity when required input(s) are not provided. 

### Database queries

Database connections are wrapped in a try catch structure, in the case where the database connection or query fails, the server will return 500 Internal Server Error instead of crashing.

### Handling data inconsistencies

Impossible dates, such as dates from more than 50 years ago or dates in the future, are detected and are not added to the database, which prevents data inconsistency.

When data is added to the database, species and latinName are checked to ensure they match which prevents data inconsistency.

## Things I could have done better with more time

* Link additional data, such as weather data to create an AI/ML model

  For example, for each tick sighting, an API could be used to get the temperatute, humidity and other types of weather data in that city at that time. After collecting this data for all tick sightings, we could train a regression model
  to determine, given the city and the estimated temperature in that city, the number of tick sightings that day, this prediction could be used to estimate the risk of tick sightings. This data could be used to warn the public if there was a particularly high risk of ticks in a certain area.

* Add a logging for errors and inconsistencies

  Adding logging for errors and data inconsistencies would allow me to record issues like invalid dates, species-Latin name mismatches, or database failures, making it easier to monitor the system, debug problems, and check the performance of the API.


