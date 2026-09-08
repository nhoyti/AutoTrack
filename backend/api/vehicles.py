"""Vehicle API endpoints for AutoTrack."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

import sys
import os
_api_dir = os.path.join(os.path.dirname(__file__), '..')
if _api_dir not in sys.path:
    sys.path.insert(0, _api_dir)

from db import get_db
from app.models import Vehicle, Customer

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("/", response_model=List[dict])
def list_vehicles(
    query: Optional[str] = None,
    customer_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List vehicles, optionally filtered by plate, VIN, or customer."""
    from sqlalchemy import select

    stmt = select(Vehicle)
    if customer_id:
        stmt = stmt.where(Vehicle.customer_id == customer_id)
    if query:
        stmt = stmt.where(
            Vehicle.plate_number.ilike(f"%{query}%")
            | Vehicle.vin_chassis_number.ilike(f"%{query}%")
        )
    vehicles = db.execute(stmt).scalars().all()
    return [
        {
            "id": v.id,
            "customer_id": v.customer_id,
            "plate_number": v.plate_number,
            "vin_chassis_number": v.vin_chassis_number,
            "make": v.make,
            "model": v.model,
            "variant": v.variant,
            "year": v.year,
            "color": v.color,
            "fuel_type": v.fuel_type,
            "transmission": v.transmission,
            "current_odometer": v.current_odometer,
        }
        for v in vehicles
    ]


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_data: dict,
    db: Session = Depends(get_db),
):
    """Create a new vehicle."""
    from ...app.models import Customer as CustomerModel

    # Check if vehicle already exists by plate number or VIN
    plate = vehicle_data.get("plate_number", "").strip()
    vin = vehicle_data.get("vin_chassis_number", "").strip()

    stmt = select(Vehicle).where(
        (Vehicle.plate_number == plate) | (Vehicle.vin_chassis_number == vin)
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this plate number or VIN already exists.",
        )

    # If customer_id provided, verify customer exists
    if customer_id:
        customer = db.get(CustomerModel, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with id {customer_id} not found.",
            )

    vehicle = Vehicle(
        customer_id=vehicle_data.get("customer_id"),
        plate_number=plate,
        vin_chassis_number=vin or None,
        make=vehicle_data.get("make", ""),
        model=vehicle_data.get("model", ""),
        variant=vehicle_data.get("variant", ""),
        year=vehicle_data.get("year", 0),
        color=vehicle_data.get("color", ""),
        fuel_type=vehicle_data.get("fuel_type", ""),
        transmission=vehicle_data.get("transmission", ""),
        current_odometer=vehicle_data.get("current_odometer", 0.0),
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return {
        "id": vehicle.id,
        "customer_id": vehicle.customer_id,
        "plate_number": vehicle.plate_number,
        "vin_chassis_number": vehicle.vin_chassis_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "variant": vehicle.variant,
        "year": vehicle.year,
        "color": vehicle.color,
        "fuel_type": vehicle.fuel_type,
        "transmission": vehicle.transmission,
        "current_odometer": vehicle.current_odometer,
    }


@router.get("/{vehicle_id}", response_model=dict)
def get_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    """Get a single vehicle by ID."""
    from ...app.models import Vehicle as VehicleModel

    vehicle = db.get(VehicleModel, vehicle_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle with id {vehicle_id} not found.",
        )
    return {
        "id": vehicle.id,
        "customer_id": vehicle.customer_id,
        "plate_number": vehicle.plate_number,
        "vin_chassis_number": vehicle.vin_chassis_number,
        "make": vehicle.make,
        "model": vehicle.model,
        "variant": vehicle.variant,
        "year": vehicle.year,
        "color": vehicle.color,
        "fuel_type": vehicle.fuel_type,
        "transmission": vehicle.transmission,
        "current_odometer": vehicle.current_odometer,
    }