# pyvalidate


## Reason for this project 
Checks if utf8 encoded data is being stored in latin1 columns. Validates if the data is valid utf8.


## How to use
```python
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
            
    python3 pyvalidate2.py -d temp -t xxxx -c 'Column Name' --fix
    
The `fix_data` function is designed to identify and print out data in a specific column of a specific table in a database that contains non-UTF8 compliant characters.

Here's a breakdown of what it does:

1. It takes four parameters: `cursor` (a MySQL cursor object for executing SQL commands), `database` (the name of the database), `table_name` (the name of the table), and `column_name` (the name of the column).

2. It executes a SQL command that does the following:
   - Selects data from the specified column in the specified table.
   - Converts the data to binary, then to latin1 and utf8.
   - Filters the data to only include rows where the binary representation of the column data contains non-UTF8 compliant characters (those with byte values between 0x80 and 0xFF).
   - The result of this command is a list of tuples, where each tuple contains two elements: the latin1 and utf8 versions of the column data.

3. It iterates over the result of the SQL command. For each tuple, it prints the latin1 version in red and the utf8 version in blue.

Please note that this function doesn't actually "fix" the data in the sense of modifying the database. It only identifies and prints out the non-UTF8 compliant data.

```
