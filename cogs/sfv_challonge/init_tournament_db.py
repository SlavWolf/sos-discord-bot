from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    discord_id = Column(Integer, primary_key=True)
    name = Column(String)
    rank = Column(String)

class Tournament(Base):
    __tablename__ = 'tournament'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    guild_id = Column(String)
    channel_id = Column(String)
    message_id = Column(String)

class Participant(Base):
    __tablename__ = 'participant'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournament.id"))
    name = Column(String)
    discord_id = Column(Integer, ForeignKey("user.discord_id"))

    tournament_relationship = relationship("Tournament", foreign_keys=[tournament_id])
    discord_relationship = relationship("User", foreign_keys=[discord_id])

class Match(Base):
    __tablename__ = 'match'
    uuid = Column(Integer, primary_key=True)
    id = Column(Integer)
    tournament_id = Column(Integer, ForeignKey("tournament.id"))
    player_id = Column(Integer, ForeignKey("participant.id"))
    score = Column(String)
    state = Column(String)

    tournament_relationship = relationship("Tournament", foreign_keys=[tournament_id])
    player_relationship = relationship("Participant", foreign_keys=[player_id])


