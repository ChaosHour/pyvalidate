#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" in a more Pythonic way
ChaosHour - Kurt Larsen
All of the queries in this script are based on the following article:
https://www.percona.com/blog/2013/10/16/utf8-data-on-latin1-tables-converting-to-utf8-without-downtime-or-double-encoding/
https://dba.stackexchange.com/questions/317425/how-can-i-detect-double-encoded-mysql-columns-and-rows-and-validate-the-repair
https://stackoverflow.com/questions/35167891/mysql-utf8mb4-encoding-issues

Credits:
Rick James
[https://dba.stackexchange.com/users/1876/rick-james]
Percona - MySQL High Performance Blog
"""

import re
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
    parser.add_argument('--fix2', action='store_true', help='Fix data2')
    parser.add_argument('--fix3', action='store_true', help='Fix data3')
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

"""
def clean_spaces(byte_sequence: str) -> str:
    #str2 = re.sub(r'\s', '', byte_sequence.decode.hex())
    str2 = re.sub(r'\s', '', byte_sequence.decode('latin-1'))
    return bytes.fromhex(str2.encode('latin-1').encode('hex'))
"""
def clean_spaces(byte_sequence: str) -> str:
    str2 = re.sub(r'\s', '', byte_sequence.decode('latin-1'))
    str2 = re.sub('\x00', '', str2)
    return bytes.fromhex(str2.encode('latin-1').hex())

"""
def remove_null_bytes(input_string: str) -> str:
    return re.sub('\x00', '', input_string)
"""

def is_unusual_latin1(sequence):
    """Check if the sequence contains unusual Latin-1 characters."""
    for char in sequence:
        if char < 0x20 or 0x7F <= char <= 0x9F:
            return True
    return False

def is_valid_utf8(byte_sequence):
    """Check if the sequence is a valid UTF-8 sequence."""
    try:
        byte_sequence.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def analyze_data(hex_string):
    """Analyze the HEX string for unusual Latin-1 but valid UTF-8 sequences."""
    bytes_sequence = bytes.fromhex(hex_string)
    c2 =  clean_spaces(bytes_sequence) 
    if is_unusual_latin1(c2) and is_valid_utf8(bytes_sequence):
        return f"Unusual Latin-1 but valid UTF-8 sequence found: {bytes_sequence.decode('utf-8')}"
    else:
        return None
    

def fix_data(cursor, database, table_name, column_name):  # Add column_name as a parameter
    cursor.execute(f"SELECT CONVERT(CONVERT(`{column_name}` USING BINARY) USING latin1) AS latin1, CONVERT(CONVERT(`{column_name}` USING BINARY) USING utf8) AS utf8 FROM `{database}`.`{table_name}` WHERE CONVERT(`{column_name}` USING BINARY) RLIKE CONCAT('[', UNHEX('80'), '-', UNHEX('FF'), ']')")
    for (latin1, utf8) in cursor:
        print(f"{colored('latin1:', 'red')} {latin1}, {colored('utf8:', 'blue')} {utf8}")


def fix_data2(cursor, database, table_name, column_name):
    cursor.execute(f"SELECT `{column_name}` FROM `{database}`.`{table_name}` WHERE HEX(`{column_name}`) RLIKE '^(..)*(F.|E2|EF)'")
    for (result,) in cursor:
        print(result)
        print(f"{colored('result:', 'red')} {result}")


def check_hex_values(cursor, database):
    cursor.execute(f"SELECT TABLE_NAME, COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = '{database}' AND DATA_TYPE IN ('char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext')")
    columns = cursor.fetchall()

    for (table_name, column_name) in columns:
        try:
            cursor.execute(f"SELECT `{column_name}`, HEX(`{column_name}`) FROM `{database}`.`{table_name}` WHERE HEX(`{column_name}`) REGEXP '(..)*[89a-fA-F]' LIMIT 5")
            results = cursor.fetchall()
            for (col, hex_col) in results:
                #print(f"{colored('Table:', 'red')} {table_name}, Column: {column_name}, Value: {col}, {colored('Hex:', 'blue')} {hex_col}")
                result = analyze_data(hex_col)
                if result:
                    print(f"{colored('Table:', 'red')} {table_name}, Column: {column_name}, Value: {col}, {colored('Hex:', 'blue')} {hex_col}")
                    print(result)
                    print("")
        except mysql.connector.errors.ProgrammingError as e:
            if 'doesn\'t exist' in str(e):
                print(f"Table {table_name} doesn't exist. Skipping...")
                continue
            else:
                raise

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
                #cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}' AND table_schema = '{database}' ORDER BY ordinal_position")
                # Modify the query to only check the column type that you want to check AND DATA_TYPE IN ('char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext')")
                cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}' AND table_schema = '{database}' AND DATA_TYPE IN ('char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext') ORDER BY ordinal_position")
                columns = cursor.fetchall()
            except mysql.connector.errors.ProgrammingError as e:
                if 'doesn\'t exist' in str(e):
                    print(f"Table {table_name} doesn't exist. Skipping...")
                    continue
                else:
                    raise

        for (column_name,) in columns:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{table_name}` WHERE LENGTH(`{column_name}`) != CHAR_LENGTH(`{column_name}`)")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"Current table: {colored(table_name, 'blue')}")
                    print(f"Column: {colored(column_name, 'blue')}")
                    print(f"Count of records that need to be fixed: {colored(str(count), 'blue')}\n")
            except mysql.connector.errors.ProgrammingError as e:
                if 'doesn\'t exist' in str(e):
                    print(f"Table {table_name} doesn't exist. Skipping...")
                    continue
                else:
                    raise

        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{database}`.`{table_name}`")
            total_rows = cursor.fetchone()[0]
        except mysql.connector.errors.ProgrammingError as e:
            if 'doesn\'t exist' in str(e):
                print(f"Table {table_name} doesn't exist. Skipping...")
                continue
            else:
                raise

        for (column_name,) in columns:
            offset = 0
            while True:
                try:
                    cursor.execute(f"SELECT `{column_name}` FROM `{database}`.`{table_name}` LIMIT {batch_size} OFFSET {offset}")
                    rows = cursor.fetchall()
                    if not rows:
                        break  # No more rows to fetch

                    # ... process the rows ...

                    offset += batch_size
                except mysql.connector.errors.ProgrammingError as e:
                    if 'doesn\'t exist' in str(e):
                        print(f"Table {table_name} doesn't exist. Skipping...")
                        break
                    else:
                        raise

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
    elif args.fix2:
        fix_data2(cursor, args.database, args.table, args.c)
    elif args.fix3:
        check_hex_values(cursor, args.database)        
    elif args.database:
        check_utf8_compliance(cursor, args.database, args.table)

    cnx.close()

if __name__ == "__main__":
    main()