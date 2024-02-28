import sqlite3
from sqlite3 import Error, Connection

from colorama import Fore, Style


def open_database(path) -> Connection:
    try:
        db = sqlite3.connect(path)
        print(f"{Fore.GREEN}{Style.BRIGHT}Successfully connected to SQL database{Fore.RESET}{Style.RESET_ALL}")
    except Error as err:
        print(f"{Fore.GREEN}COULD NOT OPEN SQLITE DATABASE:{Fore.RESET}")
        raise err
    return db


def db_execute(db: Connection, sql: str):
    # high level abstraction, do not use externally
    db_cursor = db.cursor()
    res = db_cursor.execute(sql).fetchall()
    db.commit()
    return res


def db_insert(db: Connection, table: str, values: tuple):
    # high level abstraction, do not use externally
    sql = f"INSERT INTO {table} VALUES(?" + ', ?' * (len(values)-1) + ')'
    db_cursor = db.cursor()
    res = db_cursor.execute(sql, values)
    db.commit()
    return res


def db_remove(db: Connection, table: str, condition: str):
    # high level abstraction, do not use externally
    sql = f"DELETE FROM {table} WHERE {condition}"
    db_cursor = db.cursor()
    res = db_cursor.execute(sql)
    db.commit()
    return res
