#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" in a more Pythonic way
ChaosHour - Kurt Larsen
"""


import os
import time
import argparse
from os import path
from inspect import currentframe, getframeinfo
from os import getenv, getpid, path
import mysql.connector
from termcolor import colored
from configparser import ConfigParser

def parse_arguments():
    usage_text = """
    This script performs various operations on a MySQL database.

    Usage:
        python3 pyvalidate.py [OPTIONS]

    Options:
        -s, --source    Source Host
        -d, --database  Database Name
        -t, --table     Select table
        --show          Show Databases
        --fix           Fix data

    Examples:
        Show databases:
            python3 pyvalidate.py --show

        Fix data:
            python3 pyvalidate.py --fix

        Check UTF-8 compliance for a specific database:
            python3 pyvalidate.py -d your_database_name
    """
    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('-s', '--source', help='Source Host')
    parser.add_argument('-d', '--database', help='Database Name')
    parser.add_argument('-t', '--table', help='Select table')
    parser.add_argument('-c', '--c', help='Columne Name')
    parser.add_argument('--show', action='store_true', help='Show Databases')
    parser.add_argument('--fix', action='store_true', help='Fix data')
    return parser.parse_args()

def get_client_config(file_path="~/.my.cnf"):
    """
    Parse file_path into dict
    :param file_path str: /path/to/mysql-config.txt
    Barrowed from modules/my_sql/files/move_procs.py
    """
    file_path = path.expanduser(file_path)
    cparser = ConfigParser()
    result = {}

    if path.exists(file_path):
        cparser.read(file_path)
        section = "client"
        if section in cparser.sections():
            result = cparser.items(section=section)
    config = {
        ("unix_socket" if key == "socket" else key): (
            value.strip("'") if key == "password" else value
        )
        for key, value in result
    }
    config.update({"use_pure": True, "charset": "utf8"})
    return config

def connect_to_database(config):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute("SELECT @@hostname")
    hostname = cursor.fetchone()[0]
    print(f"Connected to {config['host']} ({hostname}): {colored('✔', 'green')}")
    return cnx, cursor

def show_databases(cursor):
    cursor.execute("SHOW DATABASES")
    for (database,) in cursor:
        print(database)

def fix_data(cursor, database, table_name, column_name):  # Add column_name as a parameter
    cursor.execute(f"SELECT CONVERT(CONVERT(`{column_name}` USING BINARY) USING latin1) AS latin1, CONVERT(CONVERT(`{column_name}` USING BINARY) USING utf8) AS utf8 FROM `{database}`.`{table_name}` WHERE CONVERT(`{column_name}` USING BINARY) RLIKE CONCAT('[', UNHEX('80'), '-', UNHEX('FF'), ']')")
    for (latin1, utf8) in cursor:
        print(f"{colored('latin1:', 'red')} {latin1}, {colored('utf8:', 'blue')} {utf8}")

import time


def check_utf8_compliance(cursor, database, table=None):
    max_retries = 5
    batch_size = 1000  # Adjust this value as needed

    if table:
        tables = [(table,)]
    else:
        cursor.execute(f"SHOW TABLES FROM {database}")
        tables = cursor.fetchall()

    for (table_name,) in tables:
        for attempt in range(max_retries):
            try:
                cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}' AND table_schema = '{database}' ORDER BY ordinal_position")
                columns = cursor.fetchall()
                break
            except mysql.connector.errors.ProgrammingError as e:
                if 'doesn\'t exist' in str(e) and attempt < max_retries - 1:  # Retry if table doesn't exist
                    time.sleep(1)  # Wait for 1 second before retrying
                    continue
                else:
                    print(f"Error: {e}. Skipping table {table_name}.")
                    break

        for (column_name,) in columns:
            if isinstance(column_name, str) and column_name.isascii():
                cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{table_name}` WHERE LENGTH(`{column_name}`) != CHAR_LENGTH(`{column_name}`)")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"Current table: {table_name}")
                    print(f"Column: {column_name}")
                    print(f"Count of records that need to be fixed: {count}\n")

        cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{table_name}`")
        total_rows = cursor.fetchone()[0]

        for (column_name,) in columns:
            offset = 0
            while True:
                cursor.execute(f"SELECT `{column_name}` FROM `{database}`.`{table_name}` LIMIT {batch_size} OFFSET {offset}")
                rows = cursor.fetchall()
                if not rows:
                    break  # No more rows to fetch

                # ... process the rows ...

                offset += batch_size
                
"""
            for (value,) in rows:
                if isinstance(value, str) and not value.isascii():
                    print(colored("\nNon-UTF8 character found in table:", 'red') + f" {table_name}, column: {column_name}, value: {value}\n")
                    """
def main():
    args = parse_arguments()
    if not any(vars(args).values()):
        return

    config = get_client_config()
    cnx, cursor = connect_to_database(config)

    if args.show:
        show_databases(cursor)
    elif args.fix:
        fix_data(cursor, args.database, args.table, args.c)
    elif args.database:
        check_utf8_compliance(cursor, args.database, args.table)

    cnx.close()

if __name__ == "__main__":
    main()