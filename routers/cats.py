from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List
from store import valid_breeds
import httpx
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from models import CatDB
from database import get_db








class Cat(BaseModel):
    id: int
    name: str
    experience: int
    breed: str
    salary: int

# To create cat, you do not need id
class CatCreate(BaseModel):
    name: str
    experience: int
    breed: str
    salary: int

class CatRead(CatCreate):
    id: int

class SalaryUpdate(BaseModel):
    salary: int




router = APIRouter()


def get_valid_breeds():
    if not valid_breeds:
        raise HTTPException(status_code=503, detail="Breeds data not loaded yet")
    return valid_breeds


@router.patch("/{cat_id}", response_model=Cat)
def update_cat_salary(cat_id: int, salary_update: SalaryUpdate, db: Session = Depends(get_db)):
    cat = db.query(CatDB).filter(CatDB.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    
    cat.salary = salary_update.salary
    db.commit()
    db.refresh(cat) 
    
    return cat

@router.post("/")
def create_cat(cat_create: CatCreate,breeds: list[str] = Depends(get_valid_breeds),  db: Session = Depends(get_db),):

    if cat_create.breed not in valid_breeds:
        raise HTTPException(status_code=400, detail=f"Breed '{cat_create.breed}' is not valid")
    new_cat = CatDB(**cat_create.model_dump())  # or cat_create.dict() if model_dump deprecated
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)  # refresh to get the assigned id
    
    return new_cat

@router.delete("/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(CatDB).filter(CatDB.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    db.delete(cat)
    db.commit()
    return

@router.get("/", response_model=list[CatRead])
def list_cats(db: Session = Depends(get_db)):
    return db.query(CatDB).all()


@router.get("/{cat_id}", response_model=CatRead)
def read_cat(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(CatDB).filter(CatDB.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")
    return cat

