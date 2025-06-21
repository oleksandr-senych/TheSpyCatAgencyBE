from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base

class CatDB(Base):
    __tablename__ = "cats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    experience = Column(Integer)
    breed = Column(String)
    salary = Column(Integer)

class MissionDB(Base):
    __tablename__ = "missions"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, nullable=True)  # missions can be unassigned
    complete = Column(Boolean, default=False)

    targets = relationship("TargetDB", back_populates="mission", cascade="all, delete-orphan")


class TargetDB(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    name = Column(String, index=True)
    country = Column(String)
    notes = Column(String, default="")
    complete = Column(Boolean, default=False)

    mission = relationship("MissionDB", back_populates="targets")