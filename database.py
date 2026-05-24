import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="abha123",
    database="vehicle_service_db"
)

cursor = conn.cursor()