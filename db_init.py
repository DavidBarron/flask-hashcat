import sqlite3

conn = sqlite3.connect('spy_challenge.db')

print("Opened database successfully")

conn.execute('DROP TABLE IF EXISTS tHashcatRun;')

create_table = """
CREATE TABLE tHashcatRun
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	command VARCHAR(900) NOT NULL,
    result TEXT NOT NULL
);
"""

conn.execute(create_table)

print("created table tHashcatRun")

conn.execute('DROP TABLE IF EXISTS tEntry;')

create_table = """
CREATE TABLE tEntry
(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	filename VARCHAR(50) NOT NULL,
	status_bit INTEGER NOT NULL,
	status_text TEXT NOT NULL
);
"""

print("created table tEntry")

conn.execute(create_table)

print("Tables created successfully")

conn.close()
