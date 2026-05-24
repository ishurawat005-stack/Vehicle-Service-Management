import mysql.connector
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os

---------------- DATABASE CONNECTION ----------------

try:
conn = mysql.connector.connect(
host="127.0.0.1",
user="root",
password="abha123",
database="vehicle_service_db"
)
cursor = conn.cursor()
print(" Connected to MySQL")
except Exception as e:
print("Database Error:", e)
exit()

---------------- CUSTOMER MODULE ----------------

def add_customer():
name = input("Name: ")
phone = input("Phone: ")
vehicle = input("Vehicle Number: ")
address = input("Address: ")
purchase_date = input("Purchase Date (YYYY-MM-DD): ")
km = int(input("Current KM: "))
cursor.execute("""INSERT INTO customers
(name, phone, vehicle_number, address, purchase_date, current_km)
VALUES (%s,%s,%s,%s,%s,%s)""",
(name, phone, vehicle, address, purchase_date, km))
conn.commit()
print("Customer added! ID:", cursor.lastrowid)
def view_customers():
cursor.execute("SELECT * FROM customers")
for row in cursor.fetchall():
print(f"ID:{row[0]} | Name:{row[1]} | Vehicle:{row[3]} | KM:{row[6]}")
def search_customer():
val = input("Enter Phone or Vehicle: ")
cursor.execute("SELECT * FROM customers WHERE phone=%s OR vehicle_number=%s", (val, val))
for row in cursor.fetchall():
print(row)
def update_km():
vehicle = input("Vehicle Number: ")
km = int(input("New KM: "))
cursor.execute("UPDATE customers SET current_km=%s WHERE vehicle_number=%s", (km, vehicle))
conn.commit()
if cursor.rowcount > 0:
print("KM Updated!")
else:
print("Vehicle not found!")

---------------- SERVICE MODULE ----------------

def book_service():
vehicle = input("Vehicle Number: ")
cursor.execute("SELECT customer_id FROM customers WHERE vehicle_number=%s", (vehicle,))
data = cursor.fetchone()
if not data:
print("❌ Vehicle not found!")
return
cid = data[0]
stype = input("Service Type: ")
mech = input("Mechanic: ")
date = input("Date (YYYY-MM-DD): ")
cursor.execute("""INSERT INTO services
(customer_id, service_type, mechanic, service_date, status)
VALUES (%s,%s,%s,%s,'Pending')""",
(cid, stype, mech, date))
conn.commit()
print("Service Booked!")
def update_service():
sid = input("Service ID: ")
status = input("Status (Pending/In Progress/Completed): ")
cursor.execute("UPDATE services SET status=%s WHERE service_id=%s", (status, sid))
conn.commit()
if cursor.rowcount > 0:
print("Updated!")
else:
print("Service not found!")
def service_history():
vehicle = input("Vehicle Number: ")
cursor.execute("""
SELECT c.name, s.service_type, s.mechanic, s.service_date, s.status
FROM customers c
JOIN services s ON c.customer_id = s.customer_id
WHERE c.vehicle_number=%s
""", (vehicle,))
data = cursor.fetchall()
if not data:
print("No history found.")
else:
for row in data:
print(f"Name:{row[0]} | Service:{row[1]} | Mechanic:{row[2]} | Date:{row[3]} | Status:{row[4]}")

---------------- SPARE PARTS ----------------

def add_part():
name = input("Part Name: ")
qty = int(input("Quantity: "))
price = float(input("Price: "))
cursor.execute("INSERT INTO spare_parts VALUES (NULL,%s,%s,%s)", (name, qty, price))
conn.commit()
print("Part Added!")
def view_parts():
cursor.execute("SELECT * FROM spare_parts")
for row in cursor.fetchall():
print(f"ID:{row[0]} | {row[1]} | Qty:{row[2]} | ₹{row[3]}")
def update_part_stock():
try:
part_id = int(input("Enter Part ID: "))
cursor.execute("SELECT part_name, quantity FROM spare_parts WHERE part_id=%s", (part_id,))
part = cursor.fetchone()
if not part:
print("Part not found!")
return
name, current_qty = part
print(f"Current Stock of {name}: {current_qty}")
change = int(input("Enter quantity to ADD (+) or REMOVE (-): "))
new_qty = current_qty + change
if new_qty < 0:
print("Stock cannot be negative!")
return
cursor.execute("UPDATE spare_parts SET quantity=%s WHERE part_id=%s", (new_qty, part_id))
conn.commit()
print(f"✅ Stock updated! New Quantity: {new_qty}")

LOW STOCK ALERT

if new_qty < 5:
print(f"LOW STOCK ALERT: {name} only {new_qty} left!")
if new_qty == 0:
print(f"{name} is OUT OF STOCK!")
except Exception as e:
print("Error:", e)

---------------- SMART SERVICE ----------------

def smart_service():
vehicle = input("Vehicle Number: ")
cursor.execute("SELECT purchase_date, current_km FROM customers WHERE vehicle_number=%s", (vehicle,))
result = cursor.fetchone()
if not result:
print("Vehicle not found!")
return
purchase_date, km = result
today = datetime.today()
months = (today.year - purchase_date.year) * 12 + today.month - purchase_date.month
print("\nKM:", km, "| Months:", months)
print("\nAvailable Services:")
print("Basic, Oil Change, Full, Major")
if km > 20000 or months > 24:
print("Recommended: Major Service")
elif km > 10000 or months > 12:
print("Recommended: Full Service")
elif km > 5000 or months > 6:
print("Recommended: Oil Change")
else:
print("Recommended: Basic Service")

---------------- PDF BILL ----------------

def generate_pdf_bill():
vehicle = input("Enter Vehicle Number: ")
cursor.execute("SELECT customer_id, name FROM customers WHERE vehicle_number=%s", (vehicle,))
data = cursor.fetchone()
if not data:
print("Customer not found!")
return
cid, name = data
service_cost = float(input("Service Cost: "))
parts_details = []
total_parts_cost = 0
while True:
use = input("Use spare part? (y/n): ")
if use.lower() != 'y':
break
part_id = int(input("Part ID: "))
qty_used = int(input("Quantity Used: "))
cursor.execute("SELECT quantity, price, part_name FROM spare_parts WHERE part_id=%s", (part_id,))
part = cursor.fetchone()
if not part:
print("Part not found!")
continue
stock, price, part_name = part
if qty_used > stock:
print("Not enough stock!")
continue
new_stock = stock - qty_used
cursor.execute("UPDATE spare_parts SET quantity=%s WHERE part_id=%s", (new_stock, part_id))
cost = price * qty_used
total_parts_cost += cost
parts_details.append((part_name, qty_used, price, cost))
print(f"{part_name} used | Cost: ₹{cost}")
if new_stock < 5:
print(f"LOW STOCK: {part_name} only {new_stock} left!")
if new_stock == 0:
print(f"{part_name} OUT OF STOCK!")
total = service_cost + total_parts_cost
gst = total * 0.18
final = total + gst
cursor.execute("INSERT INTO bills VALUES (NULL,%s,%s,%s,%s,NOW())",
(cid, total, gst, final))
conn.commit()

-------- PDF GENERATION --------

doc = SimpleDocTemplate(f"bill_{cid}.pdf")
styles = getSampleStyleSheet()
content = []
content.append(Paragraph("Vehicle Service Bill", styles['Title']))
content.append(Spacer(1, 15))
content.append(Paragraph(f"Customer: {name}", styles['Normal']))
content.append(Paragraph(f"Vehicle: {vehicle}", styles['Normal']))
content.append(Spacer(1, 10))
content.append(Paragraph("---- Service Charges ----", styles['Heading3']))
content.append(Paragraph(f"Service Cost: ₹{service_cost}", styles['Normal']))
content.append(Spacer(1, 10))
content.append(Paragraph("---- Spare Parts Used ----", styles['Heading3']))
if not parts_details:
content.append(Paragraph("No spare parts used", styles['Normal']))
else:
for part in parts_details:
pname, qty, price, cost = part
content.append(Paragraph(
f"{pname} | Qty: {qty} | Price: ₹{price} | Cost: ₹{cost}",
styles['Normal']
))
content.append(Spacer(1, 10))
content.append(Paragraph(f"Total Parts Cost: ₹{total_parts_cost}", styles['Normal']))
content.append(Spacer(1, 10))
content.append(Paragraph("---- Billing ----", styles['Heading3']))
content.append(Paragraph(f"Subtotal: ₹{total}", styles['Normal']))
content.append(Paragraph(f"GST (18%): ₹{gst}", styles['Normal']))
content.append(Paragraph(f"Final Amount: ₹{final}", styles['Normal']))
doc.build(content)
os.startfile(f"bill_{cid}.pdf")
print("PDF Generated with full details!")

---------------- MENU ----------------

def main():
while True:
print("\n===== VEHICLE SERVICE SYSTEM =====")
print("1 Add Customer")
print("2 View Customers")
print("3 Search Customer")
print("4 Update KM")
print("5 Book Service")
print("6 Update Service")
print("7 Service History")
print("8 Add Part")
print("9 View Parts")
print("10 Update Part Stock")
print("11 Smart Service")
print("12 PDF Bill")
print("0 Exit")
ch = input("Choice: ")
if ch == "1": add_customer()
elif ch == "2": view_customers()
elif ch == "3": search_customer()
elif ch == "4": update_km()
elif ch == "5": book_service()
elif ch == "6": update_service()
elif ch == "7": service_history()
elif ch == "8": add_part()
elif ch == "9": view_parts()
elif ch == "10": update_part_stock()
elif ch == "11": smart_service()
elif ch == "12": generate_pdf_bill()
elif ch == "0": break
else: print("Invalid")
if name == "main":
main()

