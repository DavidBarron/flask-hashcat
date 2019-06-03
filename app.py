from flask import Flask, request, jsonify
from flask_cors import CORS
from rq import Queue
from rq.job import Job
from hashcat_worker import conn

import datetime
import subprocess
import os
import sqlite3

DB = 'spy_challenge.db'

WORDS = 'word_lists/words.txt'
WORDS_REV = 'word_lists/words_rev.txt'
ROCK_YOU = 'word_lists/rockyou.txt'
BASE64_RULE = 'rules/base64.rule'
POTFILE = '/Users/davidbarron/.hashcat/hashcat.potfile'


app = Flask(__name__)
CORS(app)

q = Queue('queue_hashcat', connection=conn)

# CREATE TABLE tEntry
# (
# 	id INTEGER PRIMARY KEY AUTOINCREMENT,
# 	filename VARCHAR(50) NOT NULL,
# 	status_bit INTEGER NOT NULL,
# 	status_text TEXT NOT NULL
# );


#####################
#     Database
#####################


def get_db_conn():
    return sqlite3.connect(DB)


def close_db(conn):
    if conn:
        conn.close()


def insert_db_hashcat_run(command, result):
    command_line = " ".join(command)
    conn = get_db_conn()
    try:
        insert_statement = f"INSERT INTO tHashcatRun(command, result) " \
                           f"VALUES('{command_line}', '{result}');"

        conn.execute(insert_statement)
        conn.commit()
    finally:
        close_db(conn)


def insert_db_entry(filename, status_bit=0, status_text=''):
    conn = get_db_conn()
    try:
        insert_statement = f"INSERT INTO tEntry(filename, status_bit, status_text) " \
                           f"VALUES('{filename}', {status_bit}, '{status_text}');"

        conn.execute(insert_statement)
        conn.commit()
    finally:
        close_db(conn)


def update_db_entry(filename, status_bit=0, status_text=''):
    conn = get_db_conn()
    try:
        update_statement = f"UPDATE tEntry " \
                           f"SET status_bit={status_bit}, status_text='{status_text}' " \
                           f"WHERE filename='{filename}';"

        conn.execute(update_statement)
        conn.commit()
    finally:
        close_db(conn)


def select_db_entries():
    conn = get_db_conn()
    try:
        select_statement = "SELECT * FROM tEntry ORDER BY ID ASC"
        cursor = conn.execute(select_statement)
        entries = [entry for entry in cursor]
        return entries
    finally:
        close_db(conn)


#####################
#     Misc. Aux
#####################


def allowed_file(filename):
    return filename.endswith('.txt')


def upload_hash_file(file):
    upload_filename = file.filename.replace('.txt', '{date:%Y-%m-%d_%H:%M:%S}.txt'.format(date=datetime.datetime.now()))
    upload_filename = upload_filename.replace(':', '_')
    upload_filename = upload_filename.replace('-', '_')
    upload_file_dest = os.getcwd() + '/upload/' + upload_filename
    file.save(upload_file_dest)
    return upload_file_dest, upload_filename


def cleanup_result(result):
    split_result = result.split('\n')
    return [entry for entry in split_result if entry.startswith('Recovered.') or entry.startswith('Recovered/Time.')]


def is_done(results):
    return results and 'Recovered.' in results[0] and '100.00%' in results[0]

    #  hashcat -m 0 hashes.txt rockyou.txt
    #  hashcat -m 0 -a 3 -d 2 -o /dev/null hashes.txt -i ?a?a?a -O


####################
#     Hashcat
####################


def clear_hashcat_potfile():
    command = ['cp', '/dev/null', POTFILE]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def hashcat_words(upload_file_dest):
    command = ['hashcat', '-m', '0', '-d', '2', '-o', '/dev/null', upload_file_dest, WORDS]
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_words_rev(upload_file_dest):
    command = ['hashcat', '-m', '0', '-d', '2', '-o', '/dev/null', upload_file_dest, WORDS_REV]
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_words_rule(upload_file_dest):
    command = ['hashcat', '-m', '0', '-d', '2', '-o', '/dev/null', '-r', BASE64_RULE, upload_file_dest, WORDS, '-O']
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_words_rev_rule(upload_file_dest):
    command = ['hashcat', '-m', '0', '-d', '2', '-o', '/dev/null', '-r', BASE64_RULE, upload_file_dest, WORDS_REV, '-O']
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_rock_you(upload_file_dest):
    command = ['hashcat', '-m', '0', '-d', '2', '-o', '/dev/null', upload_file_dest, ROCK_YOU]
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_rock_you_rule(upload_file_dest):
    # need to add '-O' flag here to limit password length otherwise Trap 6 error is raised
    command = ['hashcat', '-m', '0', '-d', '2', '-o', '/dev/null', '-r', BASE64_RULE, upload_file_dest, ROCK_YOU, '-O']
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_brute_force_5_all_char(upload_file_dest):
    command = ['hashcat', '-m', '0', '-a', '3', '-d', '2', '-o', '/dev/null', upload_file_dest, '?a?a?a?a?a', '-O']
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


def hashcat_words_combinator(upload_file_dest):
    command = ['hashcat', '-m', '0', '-a', '1', '-d', '2', '-o', '/dev/null', upload_file_dest, WORDS, WORDS, '-O']
    a = subprocess.run(command, stdout=subprocess.PIPE)
    result = a.stdout.decode('utf-8')
    insert_db_hashcat_run(command, result)
    return cleanup_result(result)


FUNCTIONS = [
    ('> Running dictionary attack using words.txt...\n', hashcat_words),
    ('> Running dictionary attack using words_rev.txt...\n', hashcat_words_rev),
    ('> Running dictionary attack using rockyou.txt...\n', hashcat_rock_you),
    ('> Running dictionary attack with base64 rules using words.txt...\n', hashcat_words_rule),
    ('> Running dictionary attack with base64 rules using words_rev.txt...\n', hashcat_words_rev_rule),
    ('> Running dictionary attack with base64 rules using rockyou.txt...\n', hashcat_rock_you_rule),
    ('> Running brute force attack with all 5 char permutations...\n', hashcat_brute_force_5_all_char),
    ('> Running combinator attack using words.txt twice (~5 mins)...\n', hashcat_words_combinator)
]


def process_file(upload_file_dest, upload_filename):
    print("Processing file...")
    try:
        clear_hashcat_potfile()
        status_text = ''
        insert_db_entry(upload_filename, 0, status_text)
        for m, f in FUNCTIONS:
            status_text += m
            results = f(upload_file_dest)
            for result in results:
                status_text += result + '\n'
            update_db_entry(upload_filename, 0, status_text)  # TODO: spamming /entries page seems to fug stuff here
            if is_done(results):
                break
        status_text += 'DONE\n'
        update_db_entry(upload_filename, 1, status_text)
    finally:
        print("Done processing file")


@app.route('/hashcat', methods=['POST'])
def post_file():
    print("posting file...")

    if 'file' not in request.files:
        message = {'message': 'No file provided'}
        response = jsonify(status_code=400, message=message)
        return response

    file = request.files['file']

    if not file:
        message = {'message': 'Could not fetch file, please try again'}
        response = jsonify(status_code=400, message=message)
        return response
    elif file.filename == '':
        message = {'message': 'Empty file name, please try again'}
        response = jsonify(status_code=400, message=message)
        return response
    elif not allowed_file(file.filename):
        message = {'message': 'Only txt files are allowed, please try again'}
        response = jsonify(status_code=415, message=message)
        return response
    else:
        upload_file_dest, upload_filename = upload_hash_file(file)
        job = q.enqueue(f=process_file, args=(upload_file_dest, upload_filename), timeout=-1, result_ttl=5000)
        job_key = job.get_id()
        message = {'message': f"{file.filename} successfully posted", 'job_key': job_key}
        response = jsonify(status_code=200, message=message)
        return response


@app.route('/entries', methods=['GET'])
def get_entries():
    entries = select_db_entries()
    return jsonify(entries)


@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)
    message = {'job_key': job_key, 'job_status': job.get_status()}
    response = jsonify(status_code=200, message=message)
    return response


if __name__ == '__main__':
    app.run()
