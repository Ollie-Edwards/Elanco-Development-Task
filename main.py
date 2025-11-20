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
