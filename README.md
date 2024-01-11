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
        --char          Show character set and collation
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
This script is a command-line utility for performing various operations on a MySQL database.

**Check Compliance**: 
If neither `--show` nor `--char` is passed, the script checks the compliance 
of the specified database (and table, if specified). It fetches all text-type 
columns from the database (or table) and checks each value for unusual 
Latin-1 and cp1252 characters. If it finds any, it prints the offending IDs, 
the original value, the decoded value, the byte array of the original value, 
and the offending character.
```