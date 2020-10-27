from sqlalchemy import Column, String, Boolean, DateTime, BigInteger
from sqlalchemy.schema import PrimaryKeyConstraint
from database import Base
# from werkzeug.security import generate_password_hash, check_password_hash


class Test(Base):
    __tablename__ = 'test'

    email = Column(String(255), unique=True, primary_key=True)
    name = Column(String(255))
    timestamp = Column(DateTime)

    def __init__(self, email=None, name=None, timestamp=None):
        self.access_token = email
        self.access_token_secret = name
        self.timestamp = timestamp  

class Employees(Base):
    __tablename__ = 'employees'

    email = Column(String(255), unique=True, primary_key=True)
    firstName = Column(String(255))
    lastName = Column(String(255))
    paycomEmployeeCode = Column(String(255))
    phoneNumber = Column(String(255))
    personalEmail = Column(String(255))

    def __init__(self, email=None, firstName=None, lastName=None, paycomEmployeeCode=None, phoneNumber=None, personalEmail=None):
        self.email = email
        self.firstName = firstName
        self.lastName = lastName  
        self.paycomEmployeeCode = paycomEmployeeCode
        self.phoneNumber = phoneNumber
        self.personalEmail = personalEmail         

class ScheduleRecon(Base):
    __tablename__ = 'schedulerecon'

    startDate = Column(DateTime, primary_key=True)
    email = Column(String(255), primary_key=True)
    firstName = Column(String(255))
    lastName = Column(String(255))
    shiftDescription = Column(String(255))
    phoneNumber = Column(String(255))
    personalEmail = Column(String(255))
    amazonShiftType = Column(String(255))

    def __init__(self, startDate=None, email=None, firstName=None, lastName=None, shiftDescription=None, phoneNumber=None, personalEmail=None, amazonShiftType=None):
        self.startDate = startDate
        self.email = email
        self.firstName = firstName
        self.lastName = lastName  
        self.shiftDescription = shiftDescription
        self.phoneNumber = phoneNumber
        self.personalEmail = personalEmail      
        self.amazonShiftType = amazonShiftType       
