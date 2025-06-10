from fastapi import APIRouter
from fastapi import FastAPI, Depends, HTTPException, status, Query, Security
from sqlmodel import select
from app.deps import SessionDep, get_current_user
from app.models import Hero, HeroCreate, HeroPublic, HeroUpdate, User


router = APIRouter(prefix="/heroes", tags=["heroes"])


@router.get("/", response_model=list[HeroPublic])
async def read_heroes(session: SessionDep):
    heroes = session.exec(select(Hero)).all()
    if not heroes:
        raise HTTPException(status_code=404, detail="No heroes found")
    return heroes

@router.get("/{hero_id}", response_model=HeroPublic)
async def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
    

@router.post("/", response_model=HeroPublic)
async def create_hero(
    hero: HeroCreate, 
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["heroes:create"])
):
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

@router.patch("/{hero_id}", response_model=HeroPublic)
async def patch_hero(
    hero_id: int, 
    hero: HeroUpdate, 
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["heroes:update"])
):
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@router.delete("/{hero_id}")
async def delete_hero(
    hero_id: int, 
    session: SessionDep,
    current_user: User = Security(get_current_user, scopes=["heroes:delete"])
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    session.delete(hero)
    session.commit()
    return {"message": "Hero deleted successfully"}

