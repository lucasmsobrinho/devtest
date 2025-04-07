import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from main import app, get_session
from models import Elevator, Floor, Demand

# Set up in-memory database for testing
@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://:memory:"
    )
    SQLModel.metadata.create_all(engine)

    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    return client

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://:memory:"
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_create_elevator(client):
    response = client.post(
        "/elevator/",
        json={"max_floor": 10, "min_floor": -2, "current_floor": 0}
    )
    assert response.status_code == 200
    data = response.json()
    print(response)
    assert data["id"] is not None
    assert data["max_floor"] == 10
    assert data["min_floor"] == -2
    assert data["current_floor"] == 0
    assert data["motion_status"] == "still"

def test_get_existing_elevator(client):
    create_response = client.post(
        "/elevator/",
        json={"max_floor": 10, "min_floor": 0, "current_floor": 0}
    )
    elevator_id = create_response.json()["id"]
    
    response = client.get(f"/elevator/{elevator_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == elevator_id
    assert data["max_floor"] == 10
    assert data["min_floor"] == 0

def test_get_nonexistent_elevator(client):
    response = client.get("/elevator/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Elevator not found"

def test_create_demand(client):
    create_elevator_response = client.post(
        "/elevator/",
        json={"max_floor": 10, "min_floor": 0, "current_floor": 0}
    )
    elevator_id = create_elevator_response.json()["id"]
    
    # Then create a demand
    response = client.post(
        "/demand/",
        json={
            "elevator_id": elevator_id,
            "source": "inside",
            "target_floor": 5
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] is not None
    assert data["elevator_id"] == elevator_id
    assert data["source"] == "inside"
    assert data["target_floor"] == 5

def test_get_demand(client):
    create_elevator_response = client.post(
        "/elevator/",
        json={"max_floor": 10, "min_floor": 0, "current_floor": 0}
    )
    elevator_id = create_elevator_response.json()["id"]
    
    create_demand_response = client.post(
        "/demand/",
        json={
            "elevator_id": elevator_id,
            "source": "outside",
            "target_floor": 3
        }
    )
    demand_id = create_demand_response.json()["id"]
    
    response = client.get(f"/demand/{demand_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == demand_id
    assert data["elevator_id"] == elevator_id
    assert data["target_floor"] == 3

def test_get_nonexistent_demand(client):
    response = client.get("/demand/999")
    assert response.status_code == 404
