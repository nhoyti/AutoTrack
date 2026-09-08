"""Customer API endpoints for AutoTrack."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

# Import from project root
sys.path.insert(0, '/Volumes/Macintosh HD - Two/projects/AutoTrack/backend')
from db import get_db
from app.models import Customer

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/", response_model=List[dict])
def list_customers(
    query: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List customers, optionally filtered by name, mobile, or email."""
    from sqlalchemy import select
    from ...app.models import Customer as CustomerModel

    stmt = select(CustomerModel)
    if query:
        stmt = stmt.where(
            CustomerModel.full_name.ilike(f"%{query}%")
            | CustomerModel.mobile_number.ilike(f"%{query}%")
            | CustomerModel.email.ilike(f"%{query}%")
        )
    customers = db.execute(stmt).scalars().all()
    return [
        {
            "id": c.id,
            "full_name": c.full_name,
            "mobile_number": c.mobile_number,
            "email": c.email,
            "address": c.address,
            "preferred_contact_method": c.preferred_contact_method,
            "status": c.status,
        }
        for c in customers
    ]


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_data: dict,
    db: Session = Depends(get_db),
):
    """Create a new customer."""
    from ...app.models import Customer as CustomerModel

    # Check if customer already exists by mobile or email
    stmt = select(CustomerModel).where(
        (CustomerModel.mobile_number == customer_data.get("mobile_number"))
        | (CustomerModel.email == customer_data.get("email"))
    )
    existing = db.execute(stmt).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this mobile number or email already exists.",
        )

    customer = CustomerModel(
        full_name=customer_data["full_name"],
        mobile_number=customer_data.get("mobile_number", ""),
        email=customer_data.get("email", ""),
        address=customer_data.get("address", ""),
        preferred_contact_method=customer_data.get("preferred_contact_method", "sms"),
        status=customer_data.get("status", "active"),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "mobile_number": customer.mobile_number,
        "email": customer.email,
        "address": customer.address,
        "preferred_contact_method": customer.preferred_contact_method,
        "status": customer.status,
    }


@router.get("/{customer_id}", response_model=dict)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
):
    """Get a single customer by ID."""
    from ...app.models import Customer as CustomerModel

    customer = db.get(CustomerModel, customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found.",
        )
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "mobile_number": customer.mobile_number,
        "email": customer.email,
        "address": customer.address,
        "preferred_contact_method": customer.pferred_contact_method,
        "status": customer.status,
    }