from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Session, create_engine, select
from models import Elevator, Demand, Floor
import uvicorn

app = FastAPI(title="Elevator Model")

DATABASE_URL = "sqlite:///./elevator.db"
engine = create_engine(DATABASE_URL)

def get_session():
    with Session(engine) as session:
        yield session

SQLModel.metadata.create_all(engine)

@app.post("/elevator/")
def create_elevator(elevator: Elevator, session: Session = Depends(get_session)):
    db_elevator = Elevator.model_validate(elevator)
    session.add(db_elevator)
    session.commit()
    for floor in range(db_elevator.min_floor, db_elevator.max_floor+1):
        db_floor = Floor(floor=floor, elevator_id=db_elevator.id)
        session.add(db_floor)
        session.commit()
    session.refresh(db_elevator)
    return db_elevator

@app.get("/elevator/{elevator_id}")
def get_elevator_status(elevator_id: int, session: Session = Depends(get_session)):
    elevator = session.get(Elevator, elevator_id)
    if not elevator:
        raise HTTPException(status_code=404, detail="Elevator not found")
    return elevator

@app.get("floors/{elevator_id}")
def get_floors_status(elevator_id: int, session: Session = Depends(get_session)):
    statement = select(Floor) \
        .where(Floor.elevator_id == elevator_id) \
        .where(Floor.is_demanded == True)
    floors = session.exec(statement)
    if len(floors) == 0:
        raise HTTPException(status_code=404, detail="No floors demanded.")
    return floors

def get_next_stop(elevator: Elevator, session: Session = Depends(get_session)):
    if elevator.motion_status == "ascending":
        next_up = session.exec(select(Floor) \
            .where(Floor.elevator_id == elevator.id) \
            .where(Floor.floor > elevator.current_floor) \
            .order_by(Floor.floor)).first()
        if next_up:
            return next_up.floor
        else:
            next_down = session.exec(select(Floor) \
                .where(Floor.elevator_id == elevator.id) \
                .where(Floor.floor < elevator.current_floor) \
                .order_by(Floor.floor)).last()
            return next_down
    elif elevator.motion_status == "ascending":
        next_down = session.exec(select(Floor) \
            .where(Floor.elevator_id == elevator.id) \
            .where(Floor.floor < elevator.current_floor) \
            .order_by(Floor.floor)).last()
        if next_down:
            return next_down.floor
        else:
            next_up = session.exec(select(Floor) \
                .where(Floor.elevator_id == elevator.id) \
                .where(Floor.floor > elevator.current_floor) \
                .order_by(Floor.floor)).first()
            return next_up.floor
    else:
        next = session.exec(select(Floor) \
            .where(Floor.elevator_id == elevator.id)).first()
        return next.floor

def change_demand_status(elevator_id: int, floor: int, new_status: bool, session: Session = Depends(get_session)):
    statement = select(Floor) \
        .where(Floor.elevator_id == elevator_id)\
        .where(Floor.floor == floor)
    floor = session.exec(statement).first()
    if floor:
        raise HTTPException(status_code=404, detail="Floor not found for the elevator.")
    
    floor.is_demanded = new_status
    session.add(floor)
    session.commit()

@app.post("elevator/{elevator_id}")
def move_elevator(elevator_id: int, session: Session = Depends(get_session)):
    # moves elevator to the next stop
    elevator = session.get(Elevator, elevator_id)
    if not elevator:
        raise HTTPException(status_code=404, detail="Elevator not found")
    if elevator.next_stop != None:
        elevator.current_floor = elevator.next_stop
        elevator.next_stop = get_next_stop(elevator)
        change_demand_status(elevator.elevator_id, elevator.current_floor, False)
        if elevator.next_stop:
            if elevator.next_stop > elevator.current_floor:
                elevator.motion_status = "ascending"
            else:
                elevator.motion_status = "descending"
        elevator.motion_status = "still"
        session.add(elevator)
        session.commit()
        session.refresh(elevator)
    else:
        raise HTTPException(status_code=400, detail="No floors demanded")
    return elevator

@app.post("/demand/")
def create_demand(demand: Demand, session: Session = Depends(get_session)):
    db_demand = Demand.model_validate(demand)
    db_floor = session.exec(select(Floor)
                            .where(Floor.elevator_id == db_demand.elevator_id)
                            .where(Floor.floor == db_demand.target_floor)).first()
    db_floor.is_demanded = True
    session.add(db_floor)
    session.add(db_demand)
    session.commit()
    session.refresh(db_demand)
    return db_demand

@app.get("/demand/{demand_id}")
def get_demand(demand_id: int, session: Session = Depends(get_session)):
    demand = session.get(Demand, demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="Demand not found")
    return demand

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
