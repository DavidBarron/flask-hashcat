import sqlite3

conn = sqlite3.connect('spy_challenge.db')

print("Opened database successfully")

cursor = conn.execute('SELECT * FROM tHashcatRun;')

for row in cursor:
    print(row)

cursor = conn.execute('SELECT * FROM tEntry;')

for row in cursor:
    print(row)

conn.close()
