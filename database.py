import uuid

from colorama import Fore, Style

from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, Table, Column, create_engine, Connection, Engine
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Session
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

# note: for now, as the response format and LLM pipeline changes rapidly, response test results / summarizations
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

    def __repr__(self) -> str:
        return (f"Applicant(id={self.id!r}, name={self.name!r}, surname={self.surname!r}, email={self.email!r}, "
                f"city={self.city!r}, phone={self.phone!r}, phone_country_code={self.phone_country_code!r}, "
                f"phone_extension={self.phone_extension!r}, country={self.country!r}, address={self.address!r}, "
                f"applications={self.applications!r})")


class Company(Base):
    __tablename__ = 'company'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    name: Mapped[str] = mapped_column(String(50))
    shortname: Mapped[Optional[str]]

    recruiters: Mapped[List['Recruiter']] = relationship(back_populates='company')

    def __repr__(self) -> str:
        return (f"Company(id={self.id!r}, name={self.name!r}, shortname={self.shortname!r}, "
                f"recruiters={self.recruiters!r})")


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

    def __repr__(self) -> str:
        return (f"Recruiter(id={self.id!r}, name={self.name!r}, surname={self.surname!r}, title={self.title!r}, "
                f"email={self.email!r}, country={self.country!r}, city={self.city!r}), "
                f"company={self.company!r}, batches={self.batches!r}")


class Batch(Base):
    __tablename__ = 'batch'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    job_title: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(300))  # intended for internal use only, a quick description

    recruiters: Mapped[List['Recruiter']] = relationship(back_populates='batches', secondary=association_table)
    applications: Mapped[List['Application']] = relationship(back_populates='batch')

    def __repr__(self) -> str:
        return (f"Batch(id={self.id!r}, job_title={self.job_title!r}, description={self.description!r}, "
                f"recruiters={self.recruiters!r}, applications={self.applications!r})")


class Application(Base):
    __tablename__ = 'application'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    applicant: Mapped['Applicant'] = relationship(back_populates='applications')
    batch: Mapped['Batch'] = relationship(back_populates='applications')
    responses: Mapped[List['Response']] = relationship(back_populates='application')

    def __repr__(self) -> str:
        return (f"Application(id={self.id!r}, applicant={self.applicant!r}, batch={self.batch!r}, "
                f"responses={self.responses!r})")


class Response(Base):
    __tablename__ = 'response'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=hashid)

    task_text: Mapped[str] = mapped_column(String(800))
    # note: for now, as the response format and LLM pipeline changes rapidly, response test results / summarizations
    #       will be kept outside the DB, in JSON files associated by ID with either the application or response

    application: Mapped['Application'] = relationship(back_populates='responses')

    def __repr__(self) -> str:
        return f"Response(id={self.id!r}, task_text={self.task_text!r}, application={self.application!r})"


engine_singleton = None


def get_engine(url='sqlite:///:memory:') -> Engine:
    global engine_singleton
    if isinstance(engine_singleton, Engine):
        return engine_singleton
    else:
        engine = create_engine(url)
        engine_singleton = engine
        return engine
