# app/routers/production.py

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    ADPProductionHouse,
    ADPProducer,
    ADPProducerHouse,
    ADPContract,
    ADPSeries,
    ADPUser,
)
from app.schemas import (
    ProductionHouseRead,
    ProductionHouseCreate,
    ProductionHouseUpdate,
    ProducerRead,
    ProducerCreate,
    ProducerUpdate,
    ContractRead,
    ContractCreate,
    ContractUpdate,
)
from app.deps import require_admin

router = APIRouter()


# =========================================================================
# PRODUCTION HOUSES
# =========================================================================

@router.get("/houses", response_model=List[ProductionHouseRead])
def list_production_houses(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all production houses."""
    houses = db.query(ADPProductionHouse).offset(skip).limit(limit).all()
    return houses


@router.get("/houses/{house_id}", response_model=ProductionHouseRead)
def get_production_house(house_id: int, db: Session = Depends(get_db)):
    """Get a production house by ID."""
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")
    return house


@router.post("/houses", response_model=ProductionHouseRead, status_code=201)
def create_production_house(
    payload: ProductionHouseCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new production house (admin only)."""
    max_id = db.query(func.max(ADPProductionHouse.house_id)).scalar()
    next_id = (max_id or 0) + 1

    house = ADPProductionHouse(
        house_id=next_id,
        name=payload.name,
        address_line1=payload.address_line1,
        city=payload.city,
        state_province=payload.state_province,
        postal_code=payload.postal_code,
        year_established=payload.year_established,
        adp_country_country_code=payload.adp_country_country_code,
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    return house


@router.patch("/houses/{house_id}", response_model=ProductionHouseRead)
def update_production_house(
    house_id: int,
    payload: ProductionHouseUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a production house (admin only)."""
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")

    if payload.name is not None:
        house.name = payload.name
    if payload.address_line1 is not None:
        house.address_line1 = payload.address_line1
    if payload.city is not None:
        house.city = payload.city
    if payload.state_province is not None:
        house.state_province = payload.state_province
    if payload.postal_code is not None:
        house.postal_code = payload.postal_code
    if payload.year_established is not None:
        house.year_established = payload.year_established

    db.commit()
    db.refresh(house)
    return house


@router.delete("/houses/{house_id}", status_code=204)
def delete_production_house(
    house_id: int,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Delete a production house (admin only)."""
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")

    # Delete related records
    db.query(ADPProducerHouse).filter(ADPProducerHouse.adp_production_house_house_id == house_id).delete()
    db.query(ADPContract).filter(ADPContract.adp_production_house_house_id == house_id).delete()

    db.delete(house)
    db.commit()


# =========================================================================
# PRODUCERS
# =========================================================================

@router.get("/producers", response_model=List[ProducerRead])
def list_producers(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all producers."""
    producers = db.query(ADPProducer).offset(skip).limit(limit).all()
    return producers


@router.get("/producers/{producer_id}", response_model=ProducerRead)
def get_producer(producer_id: int, db: Session = Depends(get_db)):
    """Get a producer by ID."""
    producer = db.query(ADPProducer).filter(ADPProducer.producer_id == producer_id).first()
    if not producer:
        raise HTTPException(status_code=404, detail="Producer not found")
    return producer


@router.post("/producers", response_model=ProducerRead, status_code=201)
def create_producer(
    payload: ProducerCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new producer (admin only)."""
    max_id = db.query(func.max(ADPProducer.producer_id)).scalar()
    next_id = (max_id or 0) + 1

    producer = ADPProducer(
        producer_id=next_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        address_line1=payload.address_line1,
        city=payload.city,
        state_province=payload.state_province,
        postal_code=payload.postal_code,
        adp_country_country_code=payload.adp_country_country_code,
    )
    db.add(producer)
    db.commit()
    db.refresh(producer)
    return producer


@router.patch("/producers/{producer_id}", response_model=ProducerRead)
def update_producer(
    producer_id: int,
    payload: ProducerUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a producer (admin only)."""
    producer = db.query(ADPProducer).filter(ADPProducer.producer_id == producer_id).first()
    if not producer:
        raise HTTPException(status_code=404, detail="Producer not found")

    if payload.first_name is not None:
        producer.first_name = payload.first_name
    if payload.last_name is not None:
        producer.last_name = payload.last_name
    if payload.email is not None:
        producer.email = payload.email
    if payload.phone is not None:
        producer.phone = payload.phone
    if payload.address_line1 is not None:
        producer.address_line1 = payload.address_line1
    if payload.city is not None:
        producer.city = payload.city
    if payload.state_province is not None:
        producer.state_province = payload.state_province
    if payload.postal_code is not None:
        producer.postal_code = payload.postal_code

    db.commit()
    db.refresh(producer)
    return producer


# =========================================================================
# CONTRACTS
# =========================================================================

@router.get("/contracts", response_model=List[ContractRead])
def list_contracts(
    status: Optional[str] = Query(None),
    series_id: Optional[int] = Query(None),
    house_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """List contracts with optional filters (admin only)."""
    q = (
        db.query(ADPContract, ADPSeries, ADPProductionHouse)
        .join(ADPSeries, ADPSeries.series_id == ADPContract.adp_series_series_id)
        .join(ADPProductionHouse, ADPProductionHouse.house_id == ADPContract.adp_production_house_house_id)
    )

    if status:
        q = q.filter(ADPContract.status == status)
    if series_id:
        q = q.filter(ADPContract.adp_series_series_id == series_id)
    if house_id:
        q = q.filter(ADPContract.adp_production_house_house_id == house_id)

    rows = q.offset(skip).limit(limit).all()

    return [
        ContractRead(
            contract_id=contract.contract_id,
            contract_start_date=contract.contract_start_date,
            contract_end_date=contract.contract_end_date,
            per_episode_charge=contract.per_episode_charge,
            status=contract.status,
            adp_series_series_id=contract.adp_series_series_id,
            adp_production_house_house_id=contract.adp_production_house_house_id,
            series_name=series.name,
            production_house_name=house.name,
        )
        for contract, series, house in rows
    ]


@router.get("/contracts/{contract_id}", response_model=ContractRead)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Get a contract by ID (admin only)."""
    row = (
        db.query(ADPContract, ADPSeries, ADPProductionHouse)
        .join(ADPSeries, ADPSeries.series_id == ADPContract.adp_series_series_id)
        .join(ADPProductionHouse, ADPProductionHouse.house_id == ADPContract.adp_production_house_house_id)
        .filter(ADPContract.contract_id == contract_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract, series, house = row
    return ContractRead(
        contract_id=contract.contract_id,
        contract_start_date=contract.contract_start_date,
        contract_end_date=contract.contract_end_date,
        per_episode_charge=contract.per_episode_charge,
        status=contract.status,
        adp_series_series_id=contract.adp_series_series_id,
        adp_production_house_house_id=contract.adp_production_house_house_id,
        series_name=series.name,
        production_house_name=house.name,
    )


@router.post("/contracts", response_model=ContractRead, status_code=201)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Create a new contract (admin only)."""
    # Validate series exists
    series = db.query(ADPSeries).filter(ADPSeries.series_id == payload.adp_series_series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")

    # Validate production house exists
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == payload.adp_production_house_house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")

    # Validate dates
    if payload.contract_end_date <= payload.contract_start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    max_id = db.query(func.max(ADPContract.contract_id)).scalar()
    next_id = (max_id or 0) + 1

    contract = ADPContract(
        contract_id=next_id,
        contract_start_date=payload.contract_start_date,
        contract_end_date=payload.contract_end_date,
        per_episode_charge=payload.per_episode_charge,
        status=payload.status,
        adp_series_series_id=payload.adp_series_series_id,
        adp_production_house_house_id=payload.adp_production_house_house_id,
    )
    db.add(contract)
    db.commit()

    return get_contract(next_id, db, admin)


@router.patch("/contracts/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    admin: ADPUser = Depends(require_admin),
):
    """Update a contract (admin only)."""
    contract = db.query(ADPContract).filter(ADPContract.contract_id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if payload.contract_start_date is not None:
        contract.contract_start_date = payload.contract_start_date
    if payload.contract_end_date is not None:
        contract.contract_end_date = payload.contract_end_date
    if payload.per_episode_charge is not None:
        contract.per_episode_charge = payload.per_episode_charge
    if payload.status is not None:
        contract.status = payload.status

    # Validate dates
    if contract.contract_end_date <= contract.contract_start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    db.commit()
    return get_contract(contract_id, db, admin)
