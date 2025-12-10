"""
Admin Router - Full CRUD for all Phase 1 entities
- Production Houses
- Producers
- Contracts
- Schedules
- Episodes
"""
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from ..deps import get_db, get_current_user, require_admin
from ..models import (
    ADPUser, ADPProductionHouse, ADPProducer, ADPProducerHouse,
    ADPContract, ADPSchedule, ADPEpisode, ADPSeries, ADPCountry
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================
# PYDANTIC SCHEMAS
# ============================================

# Production House
class ProductionHouseCreate(BaseModel):
    name: str
    address_line1: str
    
    city: str
    state_province: str
    postal_code: str
    year_established: int
    country_code: str

class ProductionHouseUpdate(BaseModel):
    name: Optional[str] = None
    address_line1: Optional[str] = None
    
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    year_established: Optional[int] = None
    country_code: Optional[str] = None

class ProductionHouseResponse(BaseModel):
    house_id: int
    name: str
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    year_established: Optional[int] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None

# Producer
class ProducerCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address_line1: str
    
    city: str
    state_province: str
    postal_code: str
    country_code: str

class ProducerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None

class ProducerResponse(BaseModel):
    producer_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state_province: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None

# Producer-House Assignment
class ProducerHouseCreate(BaseModel):
    producer_id: int
    house_id: int
    role_desc: Optional[str] = None

# Contract
class ContractCreate(BaseModel):
    contract_start_date: date
    contract_end_date: date
    per_episode_charge: float
    status: str = "ACTIVE"
    series_id: int
    house_id: int
    renewed_from_id: Optional[int] = None

class ContractUpdate(BaseModel):
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    per_episode_charge: Optional[float] = None
    status: Optional[str] = None

class ContractResponse(BaseModel):
    contract_id: int
    contract_start_date: date
    contract_end_date: date
    per_episode_charge: float
    status: str
    series_id: int
    series_name: Optional[str] = None
    house_id: int
    house_name: Optional[str] = None
    renewed_from_id: Optional[int] = None

# Schedule
class ScheduleCreate(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    total_viewers: int = 0
    tech_interrupt_yn: str = "N"
    episode_id: int

class ScheduleUpdate(BaseModel):
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    total_viewers: Optional[int] = None
    tech_interrupt_yn: Optional[str] = None

class ScheduleResponse(BaseModel):
    schedule_id: int
    start_datetime: datetime
    end_datetime: datetime
    total_viewers: int
    tech_interrupt_yn: str
    episode_id: int
    episode_title: Optional[str] = None
    series_name: Optional[str] = None

# Episode
class EpisodeCreate(BaseModel):
    episode_number: int
    title: str
    series_id: int
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = None

class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = None
    title: Optional[str] = None
    synopsis: Optional[str] = None
    runtime_minutes: Optional[int] = None

class EpisodeResponse(BaseModel):
    episode_id: int
    episode_number: int
    title: Optional[str]
    series_id: int
    series_name: Optional[str] = None
    synopsis: Optional[str]
    runtime_minutes: Optional[int]


# ============================================
# PRODUCTION HOUSE CRUD
# ============================================

@router.get("/production-houses", response_model=List[ProductionHouseResponse])
async def list_production_houses(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    houses = db.query(ADPProductionHouse).order_by(ADPProductionHouse.name).all()
    result = []
    for h in houses:
        country = db.query(ADPCountry).filter(ADPCountry.country_code == h.adp_country_country_code).first()
        result.append(ProductionHouseResponse(
            house_id=h.house_id,
            name=h.name,
            address_line1=h.address_line1,
            city=h.city,
            state_province=h.state_province,
            postal_code=h.postal_code,
            year_established=h.year_established,
            country_code=h.adp_country_country_code,
            country_name=country.country_name if country else None
        ))
    return result


@router.post("/production-houses", response_model=ProductionHouseResponse)
async def create_production_house(
    data: ProductionHouseCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    # Get next ID
    max_id = db.query(func.max(ADPProductionHouse.house_id)).scalar() or 0
    
    house = ADPProductionHouse(
        house_id=max_id + 1,
        name=data.name,
        address_line1=data.address_line1,
        city=data.city,
        state_province=data.state_province,
        postal_code=data.postal_code,
        year_established=data.year_established,
        adp_country_country_code=data.country_code
    )
    db.add(house)
    db.commit()
    db.refresh(house)
    
    country = db.query(ADPCountry).filter(ADPCountry.country_code == house.adp_country_country_code).first()
    return ProductionHouseResponse(
        house_id=house.house_id,
        name=house.name,
        address_line1=house.address_line1,
        city=house.city,
        state_province=house.state_province,
        postal_code=house.postal_code,
        year_established=house.year_established,
        country_code=house.adp_country_country_code,
        country_name=country.country_name if country else None
    )


@router.put("/production-houses/{house_id}", response_model=ProductionHouseResponse)
async def update_production_house(
    house_id: int,
    data: ProductionHouseUpdate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")
    
    if data.name is not None:
        house.name = data.name
    if data.address_line1 is not None:
        house.address_line1 = data.address_line1
    if data.city is not None:
        house.city = data.city
    if data.state_province is not None:
        house.state_province = data.state_province
    if data.postal_code is not None:
        house.postal_code = data.postal_code
    if data.year_established is not None:
        house.year_established = data.year_established
    if data.country_code is not None:
        house.adp_country_country_code = data.country_code
    
    db.commit()
    db.refresh(house)
    
    country = db.query(ADPCountry).filter(ADPCountry.country_code == house.adp_country_country_code).first()
    return ProductionHouseResponse(
        house_id=house.house_id,
        name=house.name,
        address_line1=house.address_line1,
        city=house.city,
        state_province=house.state_province,
        postal_code=house.postal_code,
        year_established=house.year_established,
        country_code=house.adp_country_country_code,
        country_name=country.country_name if country else None
    )


@router.delete("/production-houses/{house_id}")
async def delete_production_house(
    house_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")
    
    # Check for contracts
    contracts = db.query(ADPContract).filter(ADPContract.adp_production_house_house_id == house_id).count()
    if contracts > 0:
        raise HTTPException(status_code=400, detail="Cannot delete: has associated contracts")
    
    db.delete(house)
    db.commit()
    return {"message": "Production house deleted"}


# ============================================
# PRODUCER CRUD
# ============================================

@router.get("/producers", response_model=List[ProducerResponse])
async def list_producers(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    producers = db.query(ADPProducer).order_by(ADPProducer.last_name, ADPProducer.first_name).all()
    result = []
    for p in producers:
        country = db.query(ADPCountry).filter(ADPCountry.country_code == p.adp_country_country_code).first()
        result.append(ProducerResponse(
            producer_id=p.producer_id,
            first_name=p.first_name,
            last_name=p.last_name,
            email=p.email,
            phone=p.phone,
            address_line1=p.address_line1,
            city=p.city,
            state_province=p.state_province,
            postal_code=p.postal_code,
            country_code=p.adp_country_country_code,
            country_name=country.country_name if country else None
        ))
    return result


@router.post("/producers", response_model=ProducerResponse)
async def create_producer(
    data: ProducerCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    # Check email unique
    existing = db.query(ADPProducer).filter(ADPProducer.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    max_id = db.query(func.max(ADPProducer.producer_id)).scalar() or 0
    
    producer = ADPProducer(
        producer_id=max_id + 1,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        address_line1=data.address_line1,
        city=data.city,
        state_province=data.state_province,
        postal_code=data.postal_code,
        adp_country_country_code=data.country_code
    )
    db.add(producer)
    db.commit()
    db.refresh(producer)
    
    country = db.query(ADPCountry).filter(ADPCountry.country_code == producer.adp_country_country_code).first()
    return ProducerResponse(
        producer_id=producer.producer_id,
        first_name=producer.first_name,
        last_name=producer.last_name,
        email=producer.email,
        phone=producer.phone,
        address_line1=producer.address_line1,
        city=producer.city,
        state_province=producer.state_province,
        postal_code=producer.postal_code,
        country_code=producer.adp_country_country_code,
        country_name=country.country_name if country else None
    )


@router.put("/producers/{producer_id}", response_model=ProducerResponse)
async def update_producer(
    producer_id: int,
    data: ProducerUpdate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    producer = db.query(ADPProducer).filter(ADPProducer.producer_id == producer_id).first()
    if not producer:
        raise HTTPException(status_code=404, detail="Producer not found")
    
    if data.first_name is not None:
        producer.first_name = data.first_name
    if data.last_name is not None:
        producer.last_name = data.last_name
    if data.email is not None:
        existing = db.query(ADPProducer).filter(ADPProducer.email == data.email, ADPProducer.producer_id != producer_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")
        producer.email = data.email
    if data.phone is not None:
        producer.phone = data.phone
    if data.address_line1 is not None:
        producer.address_line1 = data.address_line1
    if data.city is not None:
        producer.city = data.city
    if data.state_province is not None:
        producer.state_province = data.state_province
    if data.postal_code is not None:
        producer.postal_code = data.postal_code
    if data.country_code is not None:
        producer.adp_country_country_code = data.country_code
    
    db.commit()
    db.refresh(producer)
    
    country = db.query(ADPCountry).filter(ADPCountry.country_code == producer.adp_country_country_code).first()
    return ProducerResponse(
        producer_id=producer.producer_id,
        first_name=producer.first_name,
        last_name=producer.last_name,
        email=producer.email,
        phone=producer.phone,
        address_line1=producer.address_line1,
        city=producer.city,
        state_province=producer.state_province,
        postal_code=producer.postal_code,
        country_code=producer.adp_country_country_code,
        country_name=country.country_name if country else None
    )


@router.delete("/producers/{producer_id}")
async def delete_producer(
    producer_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    producer = db.query(ADPProducer).filter(ADPProducer.producer_id == producer_id).first()
    if not producer:
        raise HTTPException(status_code=404, detail="Producer not found")
    
    # Delete producer-house associations first
    db.query(ADPProducerHouse).filter(ADPProducerHouse.adp_producer_producer_id == producer_id).delete()
    db.delete(producer)
    db.commit()
    return {"message": "Producer deleted"}


# Assign producer to house
@router.post("/producer-house")
async def assign_producer_to_house(
    data: ProducerHouseCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    existing = db.query(ADPProducerHouse).filter(
        ADPProducerHouse.adp_producer_producer_id == data.producer_id,
        ADPProducerHouse.adp_production_house_house_id == data.house_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Assignment already exists")
    
    assignment = ADPProducerHouse(
        adp_producer_producer_id=data.producer_id,
        adp_production_house_house_id=data.house_id,
        role_desc=data.role_desc
    )
    db.add(assignment)
    db.commit()
    return {"message": "Producer assigned to house"}


@router.delete("/producer-house/{producer_id}/{house_id}")
async def remove_producer_from_house(
    producer_id: int,
    house_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    assignment = db.query(ADPProducerHouse).filter(
        ADPProducerHouse.adp_producer_producer_id == producer_id,
        ADPProducerHouse.adp_production_house_house_id == house_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(assignment)
    db.commit()
    return {"message": "Assignment removed"}


# ============================================
# CONTRACT CRUD
# ============================================

@router.get("/contracts", response_model=List[ContractResponse])
async def list_contracts(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    contracts = db.query(ADPContract).order_by(ADPContract.contract_start_date.desc()).all()
    result = []
    for c in contracts:
        series = db.query(ADPSeries).filter(ADPSeries.series_id == c.adp_series_series_id).first()
        house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == c.adp_production_house_house_id).first()
        result.append(ContractResponse(
            contract_id=c.contract_id,
            contract_start_date=c.contract_start_date,
            contract_end_date=c.contract_end_date,
            per_episode_charge=float(c.per_episode_charge),
            status=c.status,
            series_id=c.adp_series_series_id,
            series_name=series.name if series else None,
            house_id=c.adp_production_house_house_id,
            house_name=house.name if house else None,
            renewed_from_id=c.renewed_from_id
        ))
    return result


@router.post("/contracts", response_model=ContractResponse)
async def create_contract(
    data: ContractCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    # Validate series and house exist
    series = db.query(ADPSeries).filter(ADPSeries.series_id == data.series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == data.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="Production house not found")
    
    max_id = db.query(func.max(ADPContract.contract_id)).scalar() or 0
    
    contract = ADPContract(
        contract_id=max_id + 1,
        contract_start_date=data.contract_start_date,
        contract_end_date=data.contract_end_date,
        per_episode_charge=data.per_episode_charge,
        status=data.status,
        adp_series_series_id=data.series_id,
        adp_production_house_house_id=data.house_id,
        renewed_from_id=data.renewed_from_id
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    
    return ContractResponse(
        contract_id=contract.contract_id,
        contract_start_date=contract.contract_start_date,
        contract_end_date=contract.contract_end_date,
        per_episode_charge=float(contract.per_episode_charge),
        status=contract.status,
        series_id=contract.adp_series_series_id,
        series_name=series.name,
        house_id=contract.adp_production_house_house_id,
        house_name=house.name,
        renewed_from_id=contract.renewed_from_id
    )


@router.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    contract = db.query(ADPContract).filter(ADPContract.contract_id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if data.contract_start_date is not None:
        contract.contract_start_date = data.contract_start_date
    if data.contract_end_date is not None:
        contract.contract_end_date = data.contract_end_date
    if data.per_episode_charge is not None:
        contract.per_episode_charge = data.per_episode_charge
    if data.status is not None:
        contract.status = data.status
    
    db.commit()
    db.refresh(contract)
    
    series = db.query(ADPSeries).filter(ADPSeries.series_id == contract.adp_series_series_id).first()
    house = db.query(ADPProductionHouse).filter(ADPProductionHouse.house_id == contract.adp_production_house_house_id).first()
    
    return ContractResponse(
        contract_id=contract.contract_id,
        contract_start_date=contract.contract_start_date,
        contract_end_date=contract.contract_end_date,
        per_episode_charge=float(contract.per_episode_charge),
        status=contract.status,
        series_id=contract.adp_series_series_id,
        series_name=series.name if series else None,
        house_id=contract.adp_production_house_house_id,
        house_name=house.name if house else None,
        renewed_from_id=contract.renewed_from_id
    )


@router.delete("/contracts/{contract_id}")
async def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    contract = db.query(ADPContract).filter(ADPContract.contract_id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(contract)
    db.commit()
    return {"message": "Contract deleted"}


# ============================================
# SCHEDULE CRUD
# ============================================

@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    schedules = db.query(ADPSchedule).order_by(ADPSchedule.start_datetime.desc()).all()
    result = []
    for s in schedules:
        episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == s.adp_episode_episode_id).first()
        series_name = None
        if episode:
            series = db.query(ADPSeries).filter(ADPSeries.series_id == episode.adp_series_series_id).first()
            series_name = series.name if series else None
        result.append(ScheduleResponse(
            schedule_id=s.schedule_id,
            start_datetime=s.start_datetime,
            end_datetime=s.end_datetime,
            total_viewers=s.total_viewers,
            tech_interrupt_yn=s.tech_interrupt_yn,
            episode_id=s.adp_episode_episode_id,
            episode_title=episode.title if episode else None,
            series_name=series_name
        ))
    return result


@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(
    data: ScheduleCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    # Validate episode exists
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == data.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Validate times
    if data.end_datetime <= data.start_datetime:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    
    max_id = db.query(func.max(ADPSchedule.schedule_id)).scalar() or 0
    
    schedule = ADPSchedule(
        schedule_id=max_id + 1,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        total_viewers=data.total_viewers,
        tech_interrupt_yn=data.tech_interrupt_yn.upper(),
        adp_episode_episode_id=data.episode_id
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    series = db.query(ADPSeries).filter(ADPSeries.series_id == episode.adp_series_series_id).first()
    
    return ScheduleResponse(
        schedule_id=schedule.schedule_id,
        start_datetime=schedule.start_datetime,
        end_datetime=schedule.end_datetime,
        total_viewers=schedule.total_viewers,
        tech_interrupt_yn=schedule.tech_interrupt_yn,
        episode_id=schedule.adp_episode_episode_id,
        episode_title=episode.title,
        series_name=series.name if series else None
    )


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    data: ScheduleUpdate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    schedule = db.query(ADPSchedule).filter(ADPSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    if data.start_datetime is not None:
        schedule.start_datetime = data.start_datetime
    if data.end_datetime is not None:
        schedule.end_datetime = data.end_datetime
    if data.total_viewers is not None:
        schedule.total_viewers = data.total_viewers
    if data.tech_interrupt_yn is not None:
        schedule.tech_interrupt_yn = data.tech_interrupt_yn.upper()
    
    db.commit()
    db.refresh(schedule)
    
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == schedule.adp_episode_episode_id).first()
    series_name = None
    if episode:
        series = db.query(ADPSeries).filter(ADPSeries.series_id == episode.adp_series_series_id).first()
        series_name = series.name if series else None
    
    return ScheduleResponse(
        schedule_id=schedule.schedule_id,
        start_datetime=schedule.start_datetime,
        end_datetime=schedule.end_datetime,
        total_viewers=schedule.total_viewers,
        tech_interrupt_yn=schedule.tech_interrupt_yn,
        episode_id=schedule.adp_episode_episode_id,
        episode_title=episode.title if episode else None,
        series_name=series_name
    )


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    schedule = db.query(ADPSchedule).filter(ADPSchedule.schedule_id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted"}


# ============================================
# EPISODE CRUD
# ============================================

@router.get("/episodes", response_model=List[EpisodeResponse])
async def list_episodes(
    series_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    query = db.query(ADPEpisode)
    if series_id:
        query = query.filter(ADPEpisode.adp_series_series_id == series_id)
    episodes = query.order_by(ADPEpisode.adp_series_series_id, ADPEpisode.episode_number).all()
    
    result = []
    for e in episodes:
        series = db.query(ADPSeries).filter(ADPSeries.series_id == e.adp_series_series_id).first()
        result.append(EpisodeResponse(
            episode_id=e.episode_id,
            episode_number=e.episode_number,
            title=e.title,
            series_id=e.adp_series_series_id,
            series_name=series.name if series else None,
            synopsis=e.synopsis,
            runtime_minutes=e.runtime_minutes
        ))
    return result


@router.post("/episodes", response_model=EpisodeResponse)
async def create_episode(
    data: EpisodeCreate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    series = db.query(ADPSeries).filter(ADPSeries.series_id == data.series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Check unique episode number
    existing = db.query(ADPEpisode).filter(
        ADPEpisode.adp_series_series_id == data.series_id,
        ADPEpisode.episode_number == data.episode_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Episode number already exists for this series")
    
    max_id = db.query(func.max(ADPEpisode.episode_id)).scalar() or 0
    
    episode = ADPEpisode(
        episode_id=max_id + 1,
        episode_number=data.episode_number,
        title=data.title,
        adp_series_series_id=data.series_id,
        synopsis=data.synopsis,
        runtime_minutes=data.runtime_minutes
    )
    db.add(episode)
    
    # Update series episode count
    series.num_episodes = db.query(ADPEpisode).filter(ADPEpisode.adp_series_series_id == data.series_id).count() + 1
    
    db.commit()
    db.refresh(episode)
    
    return EpisodeResponse(
        episode_id=episode.episode_id,
        episode_number=episode.episode_number,
        title=episode.title,
        series_id=episode.adp_series_series_id,
        series_name=series.name,
        synopsis=episode.synopsis,
        runtime_minutes=episode.runtime_minutes
    )


@router.put("/episodes/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    data: EpisodeUpdate,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    if data.episode_number is not None:
        # Check unique
        existing = db.query(ADPEpisode).filter(
            ADPEpisode.adp_series_series_id == episode.adp_series_series_id,
            ADPEpisode.episode_number == data.episode_number,
            ADPEpisode.episode_id != episode_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Episode number already exists")
        episode.episode_number = data.episode_number
    if data.title is not None:
        episode.title = data.title
    if data.synopsis is not None:
        episode.synopsis = data.synopsis
    if data.runtime_minutes is not None:
        episode.runtime_minutes = data.runtime_minutes
    
    db.commit()
    db.refresh(episode)
    
    series = db.query(ADPSeries).filter(ADPSeries.series_id == episode.adp_series_series_id).first()
    
    return EpisodeResponse(
        episode_id=episode.episode_id,
        episode_number=episode.episode_number,
        title=episode.title,
        series_id=episode.adp_series_series_id,
        series_name=series.name if series else None,
        synopsis=episode.synopsis,
        runtime_minutes=episode.runtime_minutes
    )


@router.delete("/episodes/{episode_id}")
async def delete_episode(
    episode_id: int,
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    episode = db.query(ADPEpisode).filter(ADPEpisode.episode_id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    series_id = episode.adp_series_series_id
    
    # Delete related schedules first
    db.query(ADPSchedule).filter(ADPSchedule.adp_episode_episode_id == episode_id).delete()
    db.delete(episode)
    
    # Update series episode count
    series = db.query(ADPSeries).filter(ADPSeries.series_id == series_id).first()
    if series:
        series.num_episodes = db.query(ADPEpisode).filter(ADPEpisode.adp_series_series_id == series_id).count()
    
    db.commit()
    return {"message": "Episode deleted"}


# ============================================
# DASHBOARD STATS
# ============================================

@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    user: ADPUser = Depends(require_admin)
):
    from ..models import ADPAccount, ADPFeedback
    
    return {
        "total_series": db.query(ADPSeries).count(),
        "total_episodes": db.query(ADPEpisode).count(),
        "total_accounts": db.query(ADPAccount).count(),
        "total_feedbacks": db.query(ADPFeedback).count(),
        "total_production_houses": db.query(ADPProductionHouse).count(),
        "total_producers": db.query(ADPProducer).count(),
        "total_contracts": db.query(ADPContract).count(),
        "total_schedules": db.query(ADPSchedule).count(),
        "active_contracts": db.query(ADPContract).filter(ADPContract.status == "ACTIVE").count(),
    }
