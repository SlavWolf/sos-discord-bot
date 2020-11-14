from jinja2 import Template
from sqlalchemy.sql import select
from sqlalchemy import select, func, Table, MetaData, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

url = 'sqlite:////opt/bot/db/tournaments.db'
engine = create_engine(url)
metadata = MetaData(engine)

tournament = Table('tournament', metadata, autoload=True)
participant = Table('participant', metadata, autoload=True)

session = scoped_session(sessionmaker())
session.configure(bind=engine, autoflush=False, expire_on_commit=False)


def template_description(rank: str):
    """Returns filled description template"""
    with open('./cogs/sfv_challonge/description.j2') as file_:
        template = Template(file_.read())
    return template.render(rank=rank)


def get_similar_tournaments(name: str):
    rs = (session.query(func.count(tournament.name))
          .filter(tournament.c.name.startswith(name)))
    return rs[0][0]


def add_new_tournament(id: int, name: str, guild_id: str, channel_id: str, message_id: str):
    tournament.insert().values(id=id, name=name, guild_id=guild_id, channel_id=channel_id,
                               message_id=message_id).execute()


def add_participant(id: int, tournament_id: int, name: str, discord_id: int):
    participant.insert().values(id=id, tournament_id=tournament_id, name=name, discord_id=discord_id).execute()

def delete_tournament_by_name(name: str):
    id = get_tournament_id(name)
    tournament.delete(tournament.c.name == name).execute()
    return id


def get_tournament_id(name: str):
    q = select([tournament.c.id, tournament.c.name]).where(tournament.c.name == name)
    rs = session.execute(q).fetchone()
    return rs[0]


def check_if_reaction_match(guild_id: str, channel_id: str, message_id: str):
    q = tournament.select((tournament.c.guild_id == guild_id) & (tournament.c.channel_id == channel_id) & (tournament.c.message_id == message_id))
    rs = session.execute(q).fetchone()
    return rs[0]

def get_participant_id_by_name(name: str, tournament_id: int):
    q = participant.select((participant.c.name == name) & (participant.c.tournament_id == tournament_id))
    rs = session.execute(q).fetchone()
    return rs[0]
