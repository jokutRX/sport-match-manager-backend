from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Optional, List
from datetime import datetime, timedelta
import pytz
import json
import logging
from models import MatchCreate, MatchPydantic

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: Optional[int] = Field(default=None, foreign_key="tournament.id")
    team1: str
    team2: str
    date: str
    location: str
    status: str
    score1: int
    score2: int
    shotsOnGoal1: Optional[int] = 0
    shotsOnGoal2: Optional[int] = 0
    shotsOnTarget1: Optional[int] = 0
    shotsOnTarget2: Optional[int] = 0
    yellowCards1: Optional[int] = 0
    yellowCards2: Optional[int] = 0
    redCards1: Optional[int] = 0
    redCards2: Optional[int] = 0
    corners1: Optional[int] = 0
    corners2: Optional[int] = 0
    possession1: Optional[int] = 0
    possession2: Optional[int] = 0
    start_time: Optional[str] = None
    duration: Optional[int] = None
    goalScorers1: Optional[str] = None  
    goalScorers2: Optional[str] = None  
    yellowCardPlayers1: Optional[str] = None  
    yellowCardPlayers2: Optional[str] = None  
    redCardPlayers1: Optional[str] = None  
    redCardPlayers2: Optional[str] = None  
    match_type: Optional[str] = None
    referee: Optional[str] = None
    stage: Optional[str] = None  

class Team(SQLModel):
    id: Optional[int] = None
    name: str

class Tournament(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    location: str
    startDate: str
    endDate: str
    teams: str  

class TournamentCreate(SQLModel):
    name: str
    location: str
    startDate: str
    endDate: str
    teams: List[Team]

sqlite_file_name = "matches.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    logger.info("Creating database and tables")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        raise

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://sport-match-manager-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

def get_session():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {str(e)}")
            raise


@app.post("/matches/", response_model=MatchPydantic)
async def create_match(match: MatchCreate, session: Session = Depends(get_session)):
    try:
        logger.info(f"Creating match: {match.dict()}")
        match_date = match.date
        current_time = datetime.now(pytz.UTC)
        buffer_time = current_time - timedelta(minutes=5)
        logger.info(f"Match date: {match_date}, Current time: {current_time}, Buffer time: {buffer_time}")
        if match_date < buffer_time:
            raise HTTPException(status_code=400, detail=f"Cannot create a match more than 5 minutes in the past. Provided: {match_date}, Current: {current_time}")
        
        if match.tournament_id is not None:
            tournament = session.get(Tournament, match.tournament_id)
            if not tournament:
                raise HTTPException(status_code=404, detail="Tournament not found")
        
        db_match = Match(
            **match.dict(exclude={"date", "start_time", "goalScorers1", "goalScorers2", "yellowCardPlayers1", "yellowCardPlayers2", "redCardPlayers1", "redCardPlayers2"}),
            date=match.date.isoformat(),
            start_time=match.start_time.isoformat() if match.start_time else None,
            goalScorers1=json.dumps(match.goalScorers1) if match.goalScorers1 else None,
            goalScorers2=json.dumps(match.goalScorers2) if match.goalScorers2 else None,
            yellowCardPlayers1=json.dumps(match.yellowCardPlayers1) if match.yellowCardPlayers1 else None,
            yellowCardPlayers2=json.dumps(match.yellowCardPlayers2) if match.yellowCardPlayers2 else None,
            redCardPlayers1=json.dumps(match.redCardPlayers1) if match.redCardPlayers1 else None,
            redCardPlayers2=json.dumps(match.redCardPlayers2) if match.redCardPlayers2 else None,
        )
        session.add(db_match)
        session.commit()
        session.refresh(db_match)
        logger.info(f"Match created: {db_match.id}, Stage: {db_match.stage}")
        return MatchPydantic(**db_match.dict())
    except Exception as e:
        logger.error(f"Error in create_match: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/matches/", response_model=List[MatchPydantic])
async def get_matches(session: Session = Depends(get_session)):
    try:
        logger.info("Fetching all matches")
        matches = session.exec(select(Match)).all()
        logger.info(f"Fetched {len(matches)} matches")
        return [
            MatchPydantic(
                **{
                    **match.dict(),
                    "goalScorers1": json.loads(match.goalScorers1) if match.goalScorers1 else None,
                    "goalScorers2": json.loads(match.goalScorers2) if match.goalScorers2 else None,
                    "yellowCardPlayers1": json.loads(match.yellowCardPlayers1) if match.yellowCardPlayers1 else None,
                    "yellowCardPlayers2": json.loads(match.yellowCardPlayers2) if match.yellowCardPlayers2 else None,
                    "redCardPlayers1": json.loads(match.redCardPlayers1) if match.redCardPlayers1 else None,
                    "redCardPlayers2": json.loads(match.redCardPlayers2) if match.redCardPlayers2 else None,
                }
            )
            for match in matches
        ]
    except Exception as e:
        logger.error(f"Error in get_matches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/tournaments/{tournament_id}/matches/", response_model=List[MatchPydantic])
async def get_tournament_matches(tournament_id: int, session: Session = Depends(get_session)):
    try:
        logger.info(f"Fetching matches for tournament {tournament_id}")
        matches = session.exec(select(Match).where(Match.tournament_id == tournament_id)).all()
        logger.info(f"Fetched {len(matches)} matches for tournament {tournament_id}")
        return [
            MatchPydantic(
                **{
                    **match.dict(),
                    "goalScorers1": json.loads(match.goalScorers1) if match.goalScorers1 else None,
                    "goalScorers2": json.loads(match.goalScorers2) if match.goalScorers2 else None,
                    "yellowCardPlayers1": json.loads(match.yellowCardPlayers1) if match.yellowCardPlayers1 else None,
                    "yellowCardPlayers2": json.loads(match.yellowCardPlayers2) if match.yellowCardPlayers2 else None,
                    "redCardPlayers1": json.loads(match.redCardPlayers1) if match.redCardPlayers1 else None,
                    "redCardPlayers2": json.loads(match.redCardPlayers2) if match.redCardPlayers2 else None,
                }
            )
            for match in matches
        ]
    except Exception as e:
        logger.error(f"Error in get_tournament_matches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.put("/matches/{match_id}", response_model=MatchPydantic)
async def update_match(match_id: int, match: MatchCreate, session: Session = Depends(get_session)):
    try:
        logger.info(f"Updating match {match_id}")
        db_match = session.get(Match, match_id)
        if not db_match:
            raise HTTPException(status_code=404, detail="Match not found")
        
        updated_data = match.dict(exclude_unset=True, exclude={"date", "start_time"})
        if updated_data.get("status") == "Идет" and db_match.start_time is None:
            updated_data["start_time"] = datetime.now(pytz.UTC).isoformat()
        
        if match.date:
            updated_data["date"] = match.date.isoformat()
        if match.start_time:
            updated_data["start_time"] = match.start_time.isoformat()
        
        # Сериализация списков в JSON-строки
        if "goalScorers1" in updated_data:
            updated_data["goalScorers1"] = json.dumps(updated_data["goalScorers1"]) if updated_data["goalScorers1"] else None
        if "goalScorers2" in updated_data:
            updated_data["goalScorers2"] = json.dumps(updated_data["goalScorers2"]) if updated_data["goalScorers2"] else None
        if "yellowCardPlayers1" in updated_data:
            updated_data["yellowCardPlayers1"] = json.dumps(updated_data["yellowCardPlayers1"]) if updated_data["yellowCardPlayers1"] else None
        if "yellowCardPlayers2" in updated_data:
            updated_data["yellowCardPlayers2"] = json.dumps(updated_data["yellowCardPlayers2"]) if updated_data["yellowCardPlayers2"] else None
        if "redCardPlayers1" in updated_data:
            updated_data["redCardPlayers1"] = json.dumps(updated_data["redCardPlayers1"]) if updated_data["redCardPlayers1"] else None
        if "redCardPlayers2" in updated_data:
            updated_data["redCardPlayers2"] = json.dumps(updated_data["redCardPlayers2"]) if updated_data["redCardPlayers2"] else None
        
        for key, value in updated_data.items():
            setattr(db_match, key, value)
        
        session.add(db_match)
        session.commit()
        session.refresh(db_match)
        logger.info(f"Match {match_id} updated, Stage: {db_match.stage}")
        return MatchPydantic(
            **{
                **db_match.dict(),
                "goalScorers1": json.loads(db_match.goalScorers1) if db_match.goalScorers1 else None,
                "goalScorers2": json.loads(db_match.goalScorers2) if db_match.goalScorers2 else None,
                "yellowCardPlayers1": json.loads(db_match.yellowCardPlayers1) if db_match.yellowCardPlayers1 else None,
                "yellowCardPlayers2": json.loads(db_match.yellowCardPlayers2) if db_match.yellowCardPlayers2 else None,
                "redCardPlayers1": json.loads(db_match.redCardPlayers1) if db_match.redCardPlayers1 else None,
                "redCardPlayers2": json.loads(db_match.redCardPlayers2) if db_match.redCardPlayers2 else None,
            }
        )
    except Exception as e:
        logger.error(f"Error in update_match: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Эндпоинты для турниров
@app.post("/tournaments/", response_model=Tournament)
async def create_tournament(tournament: TournamentCreate, session: Session = Depends(get_session)):
    try:
        logger.info(f"Creating tournament: {tournament.dict()}")
        db_tournament = Tournament(
            name=tournament.name,
            location=tournament.location,
            startDate=tournament.startDate,
            endDate=tournament.endDate,
            teams=json.dumps([team.dict() for team in tournament.teams])
        )
        session.add(db_tournament)
        session.commit()
        session.refresh(db_tournament)
        logger.info(f"Tournament created: {db_tournament.id}")
        return db_tournament
    except Exception as e:
        logger.error(f"Error in create_tournament: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/tournaments/", response_model=List[Tournament])
async def get_tournaments(session: Session = Depends(get_session)):
    try:
        logger.info("Fetching all tournaments")
        tournaments = session.exec(select(Tournament)).all()
        logger.info(f"Fetched {len(tournaments)} tournaments")
        return tournaments
    except Exception as e:
        logger.error(f"Error in get_tournaments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")