# pyvalidate


## Reason for this project 
Checks if utf8 encoded data is being stored in latin1 columns. Validates if the data is valid utf8.


## How to use
```python
This script performs various operations on a MySQL database.

    Usage:
        python3 pyvalidate.py [OPTIONS]

    Usage:
        python3 pyvalidate4.py [OPTIONS]

    Options:
        -s, --source    Source Host
        -d, --database  Database Name
        -t, --table     Select table
        --show          Show Databases
       

    Examples:
        Show databases:
            python3 pyvalidate4.py --show

        
        Check for records with unusual Latin-1 characters and cp1252 characters print the offending IDs:
        python3 pyvalidate4.py -d database -t table

    Examples:
        Show databases:
            python3 pyvalidate4.py --show

        show character set and collation for a specific table: 
            python3 pyvalidate.py -d database -t table --char

```

## More details on usage
```python
This script is a command-line utility for performing various operations on a MySQL database. Here's a breakdown of what it does:

1. **Argument Parsing**: The script accepts command-line arguments to specify the database and table to operate on, whether to show the character set and collation, and whether to show all databases.

2. **Configuration Loading**: The script loads MySQL client configuration from a file (default is `~/.my.cnf`).

3. **Database Connection**: The script connects to the MySQL database using the loaded configuration.

4. **Database Operations**: Depending on the passed arguments, the script performs one of the following operations:

   - **Show Databases**: If the `--show` argument is passed, the script fetches and prints all database names.
   
   - **Show Character Set and Collation**: If the `--char` argument is passed, the script fetches and prints the character set and collation for the specified database and table.
   
   - **Check Compliance**: If neither `--show` nor `--char` is passed, the script checks the compliance of the specified database (and table, if specified). It fetches all text-type columns from the database (or table) and checks each value for unusual Latin-1 and cp1252 characters. If it finds any, it prints the offending IDs, the original value, the decoded value, the byte array of the original value, and the offending character.

5. **Database Disconnection**: After performing the operations, the script disconnects from the database.

The script is designed to be run from the command line, and it prints its output to the console.

```