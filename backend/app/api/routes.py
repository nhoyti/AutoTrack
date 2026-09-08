"""API routes for AutoTrack."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...db import get_db, Base, engine, SessionLocal
from ...app.models import Customer, Vehicle, Inspection, PaintJob, ServiceRecord

# Create all tables
Base.metadata.create_all(bind=engine)

# Create routers for each resource
customers_router = APIRouter(prefix="/api/customers", tags=["customers"])
vehicles_router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])
inspections_router = APIRouter(prefix="/api/inspections", tags=["inspections"])
paintjobs_router = APIRouter(prefix="/api/paint-jobs", tags=["paint-jobs"])
services_router = APIRouter(prefix="/api/services", tags=["services"])


@customers_router.get("")
async def list_customers(
    query: str = "",
    db: Session = Depends(get_db),
):
    """List customers with optional search query."""
    from sqlalchemy import select, or_
    stmt = select(Customer)
    if query:
        stmt = stmt.where(
            or_(
                Customer.full_name.ilike(f"%{query}%"),
                Customer.mobile_number.ilike(f"%{query}%"),
                Customer.email.ilike(f"%{query}%"),
            )
        )
    customers = db.execute(stmt).scalars().all()
    return {"items": [
        {"id": c.id, "full_name": c.full_name, "mobile_number": c.mobile_number,
         "email": c.email, "vehicle_count": len(c.vehicles)}
        for c in customers
    ]}


@customers_router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer(
    full_name: str,
    mobile_number: str,
    email: str,
    db: Session = Depends(get_db),
):
    """Create a new customer."""
    from ...app.models import Customer
    customer = Customer(full_name=full_name, mobile_number=mobile_number, email=email)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {"id": customer.id, "full_name": customer.full_name,
            "mobile_number": customer.mobile_number, "email": customer.email}


@customers_router.put("/{customer_id}")
async def update_customer(
    customer_id: int,
    full_name: str = "",
    mobile_number: str = "",
    email: str = "",
    db: Session = Depends(get_db),
):
    """Update a customer."""
    from ...app.models import Customer
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if full_name:
        customer.full_name = full_name
    if mobile_number:
        customer.mobile_number = mobile_number
    if email:
        customer.email = email
    db.commit()
    db.refresh(customer)
    return {"id": customer.id, "full_name": customer.full_name,
            "mobile_number": customer.mobile_number, "email": customer.email}


@vehicles_router.get("")
async def list_vehicles(
    query: str = "",
    db: Session = Depends(get_db),
):
    """List vehicles with optional search query."""
    from sqlalchemy import select, or_
    stmt = select(Vehicle)
    if query:
        stmt = stmt.where(
            or_(
                Vehicle.plate_number.ilike(f"%{query}%"),
                Vehicle.vin_chassis_number.ilike(f"%{query}%"),
                Vehicle.make.ilike(f"%{query}%"),
            )
        )
    vehicles = db.execute(stmt).scalars().all()
    return {"items": [
        {"id": v.id, "customer_id": v.customer_id, "plate_number": v.plate_number,
         "make": v.make, "model": v.model, "year": v.year, "color": v.color,
         "vin_chassis_number": v.vin_chassis_number, "current_odometer": v.current_odometer}
        for v in vehicles
    ]}


@vehicles_router.post("", status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    customer_id: int,
    plate_number: str,
    vin_chassis_number: str = "",
    make: str = "",
    model: str = "",
    year: int = 0,
    color: str = "",
    fuel_type: str = "",
    transmission: str = "",
    current_odometer: float = 0.0,
    db: Session = Depends(get_db),
):
    """Create a new vehicle."""
    from ...app.models import Vehicle
    vehicle = Vehicle(
        customer_id=customer_id, plate_number=plate_number,
        vin_chassis_number=vin_chassis_number, make=make, model=model,
        year=year, color=color, fuel_type=fuel_type,
        transmission=transmission, current_odometer=current_odometer,
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return {"id": vehicle.id, "customer_id": vehicle.customer_id,
            "plate_number": vehicle.plate_number, "make": vehicle.make,
            "model": vehicle.model, "year": vehicle.year, "color": vehicle.color}


@vehicles_router.get("/{vehicle_id}/profile")
async def get_vehicle_profile(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    """Get vehicle profile with related data."""
    from ...app.models import Vehicle, Customer, Inspection, PaintJob, ServiceRecord
    from sqlalchemy import select, func
    
    vehicle = db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    # Get customer
    customer = db.get(Customer, vehicle.customer_id)
    
    # Get inspections
    inspections = db.execute(
        select(Inspection).where(Inspection.vehicle_id == vehicle_id)
    ).scalars().all()
    
    # Get paint jobs
    paint_jobs = db.execute(
        select(PaintJob).where(PaintJob.vehicle_id == vehicle_id)
    ).scalars().all()
    
    # Get service records
    service_records = db.execute(
        select(ServiceRecord).where(ServiceRecord.vehicle_id == vehicle_id)
    ).scalars().all()
    
    return {
        "vehicle": {
            "id": vehicle.id, "customer_id": vehicle.customer_id,
            "plate_number": vehicle.plate_number, "make": vehicle.make,
            "model": vehicle.model, "year": vehicle.year, "color": vehicle.color,
            "vin_chassis_number": vehicle.vin_chassis_number,
            "current_odometer": vehicle.current_odometer,
        },
        "customer": {
            "id": customer.id, "full_name": customer.full_name,
            "mobile_number": customer.mobile_number, "email": customer.email,
        } if customer else None,
        "inspections": [
            {
                "id": insp.id, "inspection_date": str(inspi.inspection_date),
                "odometer_reading": insp.odometer_reading, "overall_condition": insp.overall_condition,
                "customer_notes": insp.customer_notes,
            }
            for insp in inspections
        ],
        "paint_jobs": [
            {
                "id": pj.id, "job_number": pj.job_number, "job_type": pj.job_type,
                "status": pj.status, "estimated_cost": str(pj.estimated_cost)
                if pj.estimated_cost else None,
            }
            for pj in paint_jobs
        ],
        "service_summary": [
            {
                "id": sr.id, "service_date": str(sr.service_date),
                "service_type": sr.service_type, "status": sr.status,
                "total_cost": str(sr.total_cost) if sr.total_cost else None,
            }
            for sr in service_records
        ],
    }


@inspections_router.post("", status_code=status.HTTP_201_CREATED)
async def create_inspection(
    vehicle_id: int,
    inspection_date,
    odometer_reading: float,
    overall_condition: str = "",
    customer_notes: str = "",
    items: list = None,
    db: Session = Depends(get_db),
):
    """Create a new inspection for a vehicle."""
    from ...app.models import Inspection, InspectionItem
    from datetime import datetime
    
    inspection = Inspection(
        vehicle_id=vehicle_id, inspection_date=inspection_date,
        odometer_reading=odometer_reading, overall_condition=overall_condition,
        customer_notes=customer_notes,
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    
    # Create inspection items if provided
    if items:
        for item in items:
            inspection_item = InspectionItem(
                inspection_id=inspection.id,
                vehicle_area=item.get("vehicle_area", ""),
                condition_type=item.get("condition_type", ""),
                severity=item.get("severity", ""),
                requested_work=item.get("requested_work", ""),
                technician_notes=item.get("technician_notes", ""),
                recommended_action=item.get("recommended_action", ""),
            )
            db.add(inspection_item)
        db.commit()
    
    return {"id": inspection.id, "vehicle_id": inspection.vehicle_id,
            "inspection_date": str(inspection.inspection_date),
            "odometer_reading": inspection.odometer_reading,
            "overall_condition": inspection.overall_condition}


@inspections_router.get("/{inspection_id}/photos")
async def list_inspection_photos(
    inspection_id: int,
    db: Session = Depends(get_db),
):
    """List photos for an inspection."""
    from ...app.models import InspectionPhoto
    photos = db.execute(
        select(InspectionPhoto).where(InspectionPhoto.inspection_item_id == inspection_id)
    ).scalars().all()
    return {"items": [
        {"id": p.id, "storage_path": p.storage_path, "photo_type": p.photo_type,
         "caption": p.caption, "uploaded_by": p.uploaded_by}
        for p in photos
    ]}


@paintjobs_router.post("", status_code=status.HTTP_201_CREATED)
async def create_paint_job(
    vehicle_id: int,
    inspection_id: int,
    job_type: str = "",
    description: str = "",
    items: list = None,
    db: Session = Depends(get_db),
):
    """Create a new paint job from an inspection."""
    from ...app.models import PaintJob, PaintJobItem
    
    paint_job = PaintJob(
        vehicle_id=vehicle_id, inspection_id=inspection_id,
        job_type=job_type, description=description,
    )
    db.add(paint_job)
    db.commit()
    db.refresh(paint_job)
    
    # Create paint job items if provided
    if items:
        for item in items:
            paint_job_item = PaintJobItem(
                paint_job_id=paint_job.id,
                vehicle_area=item.get("vehicle_area", ""),
                service_type=item.get("service_type", ""),
                description=item.get("description", ""),
                labor_cost=item.get("labor_cost", 0.0),
                material_cost=item.get("material_cost", 0.0),
                quantity=item.get("quantity", 1),
                total_cost=item.get("total_cost", 0.0),
                status=item.get("status", "pending"),
            )
            db.add(paint_job_item)
        db.commit()
    
    return {
        "id": paint_job.id, "vehicle_id": paint_job.vehicle_id,
        "inspection_id": paint_job.inspection_id, "job_type": paint_job.job_type,
        "description": paint_job.description, "status": paint_job.status,
    }


@paintjobs_router.get("/{job_id}/status")
async def update_paint_job_status(
    job_id: int,
    status: str,
    reason: str = "",
    db: Session = Depends(get_db),
):
    """Update paint job status."""
    from ...app.models import PaintJob
    paint_job = db.get(PaintJob, job_id)
    if not paint_job:
        raise HTTPException(status_code=404, detail="Paint job not found")
    paint_job.status = status
    from datetime import datetime, timezone
    paint_job.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(paint_job)
    return {"id": paint_job.id, "status": paint_job.status, "updated_at": paint_job.updated_at.isoformat()}


@services_router.post("", status_code=status.HTTP_201_CREATED)
async def create_service_record(
    vehicle_id: int,
    service_date,
    odometer_reading: float,
    service_type: str = "",
    description: str = "",
    db: Session = Depends(get_db),
):
    """Create a new service record."""
    from ...app.models import ServiceRecord
    
    service_record = ServiceRecord(
        vehicle_id=vehicle_id, service_date=service_date,
        odometer_reading=odometer_reading, service_type=service_type,
        description=description,
    )
    db.add(service_record)
    db.commit()
    db.refresh(service_record)
    return {"id": service_record.id, "vehicle_id": service_record.vehicle_id,
            "service_date": str(service_record.service_date),
            "odometer_reading": service_record.odometer_reading,
            "service_type": service_record.service_type}


@services_router.get("/{service_id}/history")
async def get_service_history(
    service_id: int,
    db: Session = Depends(get_db),
):
    """Get service record history with items and parts."""
    from ...app.models import ServiceRecord, ServiceItem, ServicePart
    
    service_record = db.get(ServiceRecord, service_id)
    if not service_record:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    items = db.execute(
        select(ServiceItem).where(ServiceItem.service_record_id == service_id)
    ).scalars().all()
    
    parts = db.execute(
        select(ServicePart).where(ServicePart.service_record_id == service_id)
    ).scalars().all()
    
    return {
        "id": service_record.id,
        "vehicle_id": service_record.vehicle_id,
        "service_date": str(service_record.service_date),
        "odometer_reading": service_record.odometer_reading,
        "service_type": service_record.service_type,
        "description": service_record.description,
        "completed_at": str(service_record.completed_at) if service_record.completed_at else None,
        "status": service_record.status,
        "labor_cost": str(service_record.labor_cost) if service_record.labor_cost else None,
        "parts_cost": str(service_record.parts_cost) if service_record.parts_cost else None,
        "total_cost": str(service_record.total_cost) if service_record.total_cost else None,
        "recommendations": service_record.recommendations,
        "items": [
            {
                "id": item.id, "service_category": item.service_category,
                "description": item.description, "status": item.status,
                "cost": str(item.cost) if item.cost else None,
                "next_due_odometer": item.next_due_odometer,
                "next_due_date": str(item.next_due_date) if item.next_due_date else None,
                "rule_type": item.rule_type,
            }
            for item in items
        ],
        "parts": [
            {
                "id": part.id, "part_name": part.part_name,
                "part_number": part.part_number, "quantity": part.quantity,
                "unit_cost": str(part.unit_cost) if part.unit_cost else None,
                "total_cost": str(part.total_cost) if part.total_cost else None,
            }
            for part in parts
        ],
    }


# Main API router
api_router = APIRouter()
api_router.include_router(customers_router)
api_router.include_router(vehicles_router)
api_router.include_router(inspections_router)
api_router.include_router(paintjobs_router)
api_router.include_router(services_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AutoTrack API",
        "docs": "/docs",
        "version": "0.1.0",
    }
