from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlmodel import select
from app.deps import SessionDep
from app.models import Hero, HeroCreate, HeroPublic, HeroUpdate


router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("/heroes", response_model=list[HeroPublic])
async def read_heroes(session: SessionDep):
    heroes = session.exec(select(Hero)).all()
    return heroes

@router.get("/heroes/{hero_id}", response_model=HeroPublic)
async def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
    

@router.post("/heroes", response_model=HeroPublic)
async def create_hero(hero: HeroCreate, session: SessionDep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

# @router.put("/heroes/{hero_id}", response_model=HeroPublic)
# def update_hero(hero_id: int, hero: Hero):
#     with Session(engine) as session:
#         db_hero = session.get(Hero, hero_id)
#         if not db_hero:
#             raise HTTPException(status_code=404, detail="Hero not found")
        
#         # update the hero
#         hero_data = hero.model_dump(exclude_unset=True)

@router.patch("/heroes/{hero_id}", response_model=HeroPublic)
async def patch_hero(hero_id: int, hero: HeroUpdate, session: SessionDep):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@router.delete("/heroes/{hero_id}")
async def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    session.delete(hero)
    session.commit()
    return {"message": "Hero deleted successfully"}

