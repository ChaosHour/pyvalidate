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
