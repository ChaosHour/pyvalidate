#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" in a more Pythonic way
ChaosHour - Kurt Larsen
"""

import re
import os
import sys
import time
import argparse
from os import path
from inspect import currentframe, getframeinfo
from os import getenv, getpid, path
import mysql.connector
from mysql.connector import errors
from termcolor import colored
from configparser import ConfigParser

def parse_arguments():
    usage_text = """
    This script performs various operations on a MySQL database.

    Usage:
        python3 pyvalidate4.py [OPTIONS]

    Options:
        -s, --source    Source Host
        -d, --database  Database Name
        -t, --table     Select table
        --char          Show character set and collation
        --show          Show Databases
       

    Examples:
        Show databases:
            python3 pyvalidate4.py --show

        
        Check for records with unusual Latin-1 characters and cp1252 characters print the offending IDs:
        python3 pyvalidate4.py -d database -t table
    """
    parser = argparse.ArgumentParser(description=usage_text)
    parser.add_argument('-s', '--source', help='Source Host')
    parser.add_argument('-d', '--database', help='Database Name')
    parser.add_argument('-t', '--table', help='Select table')
    parser.add_argument('--char', action='store_true', help='Show character set and collation')
    parser.add_argument('--show', action='store_true', help='Show Databases')
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

def get_table_charset_and_collation(cursor, database, table):
    cursor.execute(f"SELECT CCSA.character_set_name, CCSA.collation_name FROM INFORMATION_SCHEMA.`TABLES` T, INFORMATION_SCHEMA.`COLLATION_CHARACTER_SET_APPLICABILITY` CCSA WHERE CCSA.collation_name = T.table_collation AND T.table_schema = '{database}' AND T.table_name = '{table}'")
    charset, collation = cursor.fetchone()
    return charset, collation

def is_unusual_latin1(sequence: bytearray):
    """Check if the sequence contains unusual Latin-1 characters."""
    return any((char > 255) or (128 <= char <= 159) for char in sequence)

def is_unusual_cp1252(sequence: bytearray):
    """Check if the sequence contains unusual cp1252 characters."""
    return any((char > 255) or char in [129, 141, 143, 144, 157] for char in sequence)

def check_compliance(cursor, database, table=None, show_charset=False):
    start_time = time.time()  # Start the timer

    max_retries = 5
    batch_size = 80000  # Adjust this value as needed
    offending_ids = []  # List to store offending IDs
    count = 0

    if table:
        tables = [(table,)]
    else:
        cursor.execute(f"SHOW TABLES FROM {database}")
        tables = cursor.fetchall()

    for (table_name,) in tables:
        charset, collation = get_table_charset_and_collation(cursor, database, table_name)
        if show_charset:
            print(f"Character set: {charset}, Collation: {collation}")
        for attempt in range(max_retries):
            try:
                cursor.execute(f"SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = '{table_name}' AND table_schema = '{database}' AND DATA_TYPE IN ('char', 'varchar', 'tinytext', 'text', 'mediumtext', 'longtext') ORDER BY ordinal_position")
                columns = cursor.fetchall()
            except errors.ProgrammingError as e:
                if 'doesn\'t exist' in str(e):
                    print(f"Table {table_name} doesn't exist. Skipping...")
                    continue
                else:
                    raise

        for (column_name,) in columns:
            cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table_name}' AND CONSTRAINT_NAME = 'PRIMARY'")
            primary_key_results = cursor.fetchall()
            if not primary_key_results:
                print(f"Table {table_name} has no primary key. Exiting...")
                return
            else:
                primary_keys = [result[0] for result in primary_key_results]
                primary_key_str = ', '.join(f"`{key}`" for key in primary_keys)

            cursor.execute(f"SELECT MIN({primary_key_str}), MAX({primary_key_str}) FROM {database}.{table_name}")
            min_id, max_id = cursor.fetchone()
            num_chunks = (max_id - min_id) // batch_size + 1

            for chunk in range(num_chunks):
                start_id = min_id + chunk * batch_size
                end_id = start_id + batch_size - 1
                if chunk == num_chunks - 1:
                    end_id = max_id

                cursor.execute(f"SELECT `{column_name}`, {primary_key_str} FROM `{database}`.`{table_name}` WHERE {primary_key_str} BETWEEN {start_id} AND {end_id}")
                rows = cursor.fetchall()

                for row in rows:
                    value, *ids = row
                    if value is not None:
                        latin1_sequence = cp1252_sequence = None  # Define variables with a default value
                        try:
                            latin1_sequence = value.encode('latin1')
                            cp1252_sequence = value.encode('cp1252')
                        except UnicodeEncodeError:
                            latin1_sequence = value.encode('latin1', 'ignore')  # ignore characters that can't be encoded
                            cp1252_sequence = value.encode('cp1252', 'ignore')  # ignore characters that can't be encoded

                        if latin1_sequence and is_unusual_latin1(latin1_sequence) or cp1252_sequence and is_unusual_cp1252(cp1252_sequence):
                            offending_ids.append(ids)
                            count += 1

        if count > 0:
            print(f"\nCurrent table: {table_name}")
            print(f"Column: {column_name}")
            print(f"Count of records that need to be fixed: {count}\n")
            print("Offending IDs:")
            print(tuple(offending_ids))
            print("\n")

    end_time = time.time()  # Stop the timer
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print(f"Time taken: {elapsed_time} seconds")
                             
def main():
    try:
        args = parse_arguments()
        if not any(vars(args).values()):
            return

        config = get_client_config()
        cnx, cursor = connect_to_database(config)

        if args.show:
            show_databases(cursor)
        elif args.database and args.table:
            if args.char:
                charset, collation = get_table_charset_and_collation(cursor, args.database, args.table)
                print(f"Character set: {charset}, Collation: {collation}")
            else:
                check_compliance(cursor, args.database, args.table, show_charset=args.char)
        else:
            print("Error: -d/--database and -t/--table are required if not using --show")
            sys.exit(1)

        cnx.close()
    except KeyboardInterrupt:
        print("\nExecution interrupted by user. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()