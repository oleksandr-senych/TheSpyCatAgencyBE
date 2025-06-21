from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from database import get_db
from models import CatDB, MissionDB, TargetDB
router = APIRouter()

class TargetCreate(BaseModel):
    name: str
    country: str
    notes: Optional[str] = ""
    complete: bool = False

class MissionCreate(BaseModel):
    cat_id: int 
    targets: List[TargetCreate] = Field(..., min_items=1, max_items=3)

class Target(BaseModel):
    id: int
    name: str
    country: str
    notes: Optional[str] = None
    complete: bool

class TargetUpdate(BaseModel):
    notes: Optional[str] = None
    complete: Optional[bool] = None


class Mission(BaseModel):
    id: int
    #there can be unassigned missions
    cat_id: Optional[int] = None
    targets: List[Target]
    complete: bool = False

@router.post("/", response_model=Mission)
def create_mission(mission_create: MissionCreate, db: Session = Depends(get_db)):
    #cat with cat_id should be in cats table
    if mission_create.cat_id is not None:
        cat = db.query(CatDB).filter(CatDB.id == mission_create.cat_id).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Cat not found")
    #targer count validation
    if not (1 <= len(mission_create.targets) <= 3):
        raise HTTPException(status_code=400, detail="Mission must have between 1 and 3 targets")

    new_mission = MissionDB(cat_id=mission_create.cat_id, complete=False)
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)

    for target_data in mission_create.targets:
        target = TargetDB(
            mission_id=new_mission.id,
            name=target_data.name,
            country=target_data.country,
            notes=target_data.notes,
            complete=target_data.complete
        )
        db.add(target)

    db.commit()
    db.refresh(new_mission)  

    return new_mission


@router.get("/", response_model=List[Mission])
def list_missions(db: Session = Depends(get_db)):
    missions = db.query(MissionDB).all()
    return missions

@router.get("/{mission_id}", response_model=Mission)
def get_mission(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(MissionDB).filter(MissionDB.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(mission_id: int, db: Session = Depends(get_db)):
    mission = db.query(MissionDB).filter(MissionDB.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    if mission.cat_id is not None:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete a mission that is assigned to a cat"
        )

    db.delete(mission)
    db.commit()
    return


# There are 2 approaches : either the cat has multiple missions, with only one uncompleted, or after mission is marked as completed, 
# the cat is unassigned from it. Since mission history should be valuable, I chose second approach.
@router.post("/{mission_id}/assign/{cat_id}", response_model=Mission)
def assign_cat_to_mission(mission_id: int, cat_id: int, db: Session = Depends(get_db)):
    # Check if mission exists
    mission = db.query(MissionDB).filter(MissionDB.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Check if cat exists
    cat = db.query(CatDB).filter(CatDB.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Cat not found")

    # Check if the cat already has an uncompleted mission
    existing_mission = db.query(MissionDB).filter(
        MissionDB.cat_id == cat_id,
        MissionDB.complete == False
    ).first()

    if existing_mission and existing_mission.id != mission_id:
        raise HTTPException(
            status_code=400,
            detail=f"Cat already has an uncompleted mission with ID {existing_mission.id}"
        )

    # Assign the cat to the mission
    mission.cat_id = cat_id
    db.commit()
    db.refresh(mission)

    return mission

@router.patch("/targets/{target_id}", response_model=Target)
def update_target(target_id: int, update: TargetUpdate, db: Session = Depends(get_db)):
    target = db.query(TargetDB).filter(TargetDB.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # Rule: Cannot update notes if target is already complete
    if update.notes is not None and target.complete:
        raise HTTPException(status_code=400, detail="Cannot update notes of a completed target")

    if update.notes is not None:
        target.notes = update.notes

    # Always update completion state
    target.complete = update.complete

    # If completed, check if mission should also be marked as complete
    if update.complete is not None:
        target.complete = update.complete

        # If target is now complete, check if the mission should be marked as complete
        if target.complete:
            mission = db.query(MissionDB).filter(MissionDB.id == target.mission_id).first()
            if mission and all(t.complete for t in mission.targets):
                mission.complete = True


    db.commit()
    db.refresh(target)
    return target