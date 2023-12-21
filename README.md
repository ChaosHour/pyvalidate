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


python3 pyvalidate2.py -d temp -t xxxx -c 'Upper Case' --fix


```

## More 
```python
The script `pyvalidate.py` is a command-line utility for interacting with a MySQL database. Here's what each option does:

- `-s, --source`: This option allows you to specify the source host of the MySQL database.

- `-d, --database`: This option allows you to specify the name of the database you want to interact with.

- `-t, --table`: This option allows you to specify a particular table within the database that you want to interact with.

- `--show`: This option, when used, will trigger the script to fetch and display all the databases present in the MySQL server.

- `--fix`: This option, when used, will trigger the script to execute a SQL query that converts the data in a specified column of a specified table from binary to latin1 and utf8, and prints the results.

Here are the examples explained:

- `python3 pyvalidate.py --show`: This command will show all databases in the MySQL server.

- `python3 pyvalidate.py -d your_database_name`: This command will check if the data in all tables of the specified database (`your_database_name`) is UTF-8 compliant.

- `python3 pyvalidate.py -d your_database_name -t your_table_name`: This command will check if the data in the specified table (`your_table_name`) of the specified database (`your_database_name`) is UTF-8 compliant.

- `python3 pyvalidate.py -d your_database_name -t your_table_name -c your_column_name --fix` This command will convert the data in the specified column (`your_column_name`) of the specified table (`your_table_name`) of the specified database (`your_database_name`) from binary to latin1 and utf8, and print the results.
```