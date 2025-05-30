from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MatchCreate(BaseModel):
    tournament_id: Optional[int] = None
    team1: str
    team2: str
    date: datetime
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
    start_time: Optional[datetime] = None
    duration: Optional[int] = None
    goalScorers1: Optional[List[str]] = None
    goalScorers2: Optional[List[str]] = None
    yellowCardPlayers1: Optional[List[str]] = None
    yellowCardPlayers2: Optional[List[str]] = None
    redCardPlayers1: Optional[List[str]] = None
    redCardPlayers2: Optional[List[str]] = None
    match_type: Optional[str] = None
    referee: Optional[str] = None
    stage: Optional[str] = None

class MatchPydantic(MatchCreate):
    id: Optional[int] = None

    class Config:
        orm_mode = True