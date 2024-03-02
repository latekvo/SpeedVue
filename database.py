import sqlite3
from sqlite3 import Error, Connection
import uuid

from colorama import Fore, Style

from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

""" scheme: (*optional)
companies <- batches <- applications <- responses
companies <- recruiters
applicants

- companies [id, name, *shortname] 
- batches [id, company_id, job_title, recruiters_id]
- applications [id, batch_id, applicant_id]
- responses [id, application_id, task_text] (filename bound to this id)
- recruiters [id, company_id, position, email, country, city] (these accounts are hard-bound to a company) 
- applicants [id, email, name, surname, phone, phone_country_code, country, city, address]

# note: for now, as the response format, and LLM pipeline changes rapidly, response test results / summarizations
        will be kept outside of the DB, in JSON files associated by ID with both the application.id and response.id
"""


def hashid():
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


# basic table used for joining many-to-many tables by id
association_table = Table(
    "association_table",
    Base.metadata,
    Column("left_id", ForeignKey("left_table.id"), primary_key=True),
    Column("right_id", ForeignKey("right_table.id"), primary_key=True),
)


class Applicant(Base):
    __tablename__ = 'applicant'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    name: Mapped[str] = mapped_column(String(30))
    surname: Mapped[str] = mapped_column(String(30))
    email: Mapped[str] = mapped_column(String(60))
    phone: Mapped[str] = mapped_column(String(15))  # verified max length
    phone_country_code: Mapped[str] = mapped_column(String(4))
    phone_extension: Mapped[str] = mapped_column(String(11))  # verified max length
    country: Mapped[str] = mapped_column(String(20))  # common names should not be longer than this
    city: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(70))

    applications: Mapped[List['Application']] = relationship(back_populates='applicant')


class Company(Base):
    __tablename__ = 'company'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    name: Mapped[str] = mapped_column(String(50))
    shortname: Mapped[Optional[str]]

    recruiters: Mapped[List['Recruiter']] = relationship(back_populates='company')


class Recruiter(Base):
    __tablename__ = 'recruiter'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    name: Mapped[str] = mapped_column(String(30))
    surname: Mapped[str] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(60))
    country: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(30))

    company: Mapped['Company'] = relationship(back_populates='recruiters')
    batches: Mapped[List['Batch']] = relationship(back_populates='recruiters', secondary=association_table)


class Batch(Base):
    __tablename__ = 'batch'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    job_title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300))  # intended for internal use only, a quick description

    recruiters: Mapped[List['Recruiter']] = relationship(back_populates='batches', secondary=association_table)
    applications: Mapped[List['Application']] = relationship(back_populates='batch')


class Application(Base):
    __tablename__ = 'application'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    applicant: Mapped['Applicant'] = relationship(back_populates='applications')
    batch: Mapped['Batch'] = relationship(back_populates='applications')
    responses: Mapped[List['Response']] = relationship(back_populates='application')


class Response(Base):
    __tablename__ = 'response'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    task_text: Mapped[str] = mapped_column(String(800))

    application: Mapped['Application'] = relationship(back_populates='responses')


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
