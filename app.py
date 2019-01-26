from flask import Flask, request, render_template, Response, stream_with_context
import datetime
import subprocess
import os
import sqlite3
import threading

DB = 'spy_challenge.db'

HOME_PAGE = 'home.html'
RESULTS_HEADER_PAGE = 'results_header.html'
RESULTS_HISTORY_HEADER_PAGE = 'results_history_header.html'
RESULTS_ENTRY_PAGE = 'results_entry.html'

WORDS = 'word_lists/words.txt'
WORDS_REV = 'word_lists/words_rev.txt'
ROCK_YOU = 'word_lists/rockyou.txt'
BASE64_RULE = 'rules/base64.rule'
POTFILE = '/Users/davidbarron/.hashcat/hashcat.potfile'


app = Flask(__name__)

HASH_LOCK = threading.Lock()  # hashcat is pretty resource intensive, want to only be processing 1 file at a time


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


def process_file_streamed_response(upload_file_dest, filename):
    def generate():
        HASH_LOCK.acquire()
        try:
            clear_hashcat_potfile()
            yield render_template(RESULTS_HEADER_PAGE, filename=filename)
            status_text = ''
            insert_db_entry(filename, 0, status_text)
            for m, f in FUNCTIONS:
                status_text += m
                yield render_template(RESULTS_ENTRY_PAGE, messages=[m])
                results = f(upload_file_dest)
                for result in results:
                    status_text += result + '\n'
                yield render_template(RESULTS_ENTRY_PAGE, messages=results)
                update_db_entry(filename, 0, status_text)  # TODO: spamming /entries page seems to fug stuff here
                if is_done(results):
                    break
            status_text += 'DONE\n'
            update_db_entry(filename, 1, status_text)
            yield render_template(RESULTS_ENTRY_PAGE, messages=['> DONE\n'])
        finally:
            HASH_LOCK.release()

    return Response(stream_with_context(generate()))


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template(HOME_PAGE)
        file = request.files['file']
        if not file:
            return render_template(HOME_PAGE, message='Could not fetch file, please try again')
        elif file.filename == '':
            return render_template(HOME_PAGE, message='Empty file name, please try again')
        elif not allowed_file(file.filename):
            return render_template(HOME_PAGE, message='Only txt files are allowed, please try again')
        else:
            upload_file_dest, upload_filename = upload_hash_file(file)
            return process_file_streamed_response(upload_file_dest, upload_filename)

    return render_template(HOME_PAGE)


@app.route('/entries', methods=['GET'])
def get_entries():
    def generate():
        entries = select_db_entries()
        for entry in entries:
            yield render_template(RESULTS_HISTORY_HEADER_PAGE, filename=entry[1])
            yield render_template(RESULTS_ENTRY_PAGE, messages=entry[3].split('\n'))
    return Response(stream_with_context(generate()))


if __name__ == '__main__':
    app.run()
