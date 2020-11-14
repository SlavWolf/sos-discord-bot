from configparser import ConfigParser
import json
import random
import datetime

from discord.ext import commands
import discord
import challonge
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import sqlite3

from cogs.sfv_challonge.init_tournament_db import Base

DB_PATH = '/opt/bot/db/tournaments.db'
DB_URL = "sqlite:///{}".format(DB_PATH)
with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT SQLITE_VERSION()')
    data = cursor.fetchone()
    print("SQLite version:", data)
engine = create_engine(DB_URL)
Base.metadata.create_all(engine)
from cogs.sfv_challonge.helpers import *

config = ConfigParser()
config.read("configs/challonge.ini")
API_NAME = config['API']['name']
API_KEY = config['API']['token']


challonge.set_credentials(API_NAME, API_KEY)

class SFVTournamentCog(commands.Cog):
    """SFVTournamentCog"""

    def __init__(self, bot):
        self.bot = bot
        self.tournament_dict = dict()
        self.message_id = dict()
        self.JSON_PATH = "./cogs/sfv_challonge/tournaments.json"
        self.JSON_PATH_MSG = "./cogs/sfv_challonge/msg.json"

    @commands.Cog.listener()
    async def on_ready(self):
        """Make sure that DB exists and have correct tables"""
        engine = create_engine(DB_URL)
        session = scoped_session(sessionmaker())
        session.configure(bind=engine, autoflush=False, expire_on_commit=False)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, ctx):
        t_id = False
        try:
            t_id = check_if_reaction_match(ctx.guild_id, ctx.channel_id, ctx.message_id)
        except Exception as e:
            print(e)
            raise

        channel = await self.bot.fetch_channel(ctx.channel_id)
        message = await channel.fetch_message(ctx.message_id)
        author = int(message.author.mention[2:-1])
        user = self.bot.get_user(ctx.member.id)

        if t_id and author == self.bot.user.id and ctx.emoji.name == "✅":
            try:
                participant = challonge.participants.create(t_id, ctx.member.name)
                add_participant(participant['id'], tournament_id=t_id, name=ctx.member.name, discord_id=user.id)
                await user.send("You are registered now.")
            except challonge.api.ChallongeException as e:
                await user.send(e)
                raise
        elif author == self.bot.user.id and ctx.emoji.name == "✅":
            await user.send("That's either not tournament message or that tournament doesn't exist. Contact Vuk.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, ctx):
        t_id = False
        try:
            t_id = check_if_reaction_match(ctx.guild_id, ctx.channel_id, ctx.message_id)
        except Exception as e:
            print(e)
            raise

        channel = await self.bot.fetch_channel(ctx.channel_id)
        message = await channel.fetch_message(ctx.message_id)
        author = int(message.author.mention[2:-1])
        user = self.bot.get_user(ctx.user_id)
        participant_id = get_participant_id_by_name(user.name, t_id)
        if t_id and author == self.bot.user.id and ctx.emoji.name == "✅":
            try:
                challonge.participants.destroy(t_id, participant_id)
                await user.send("You are unregistered now.")
            except challonge.api.ChallongeException as e:
                await user.send(e)
                raise
        elif author == self.bot.user.id and ctx.emoji.name == "✅":
            await user.send("That's either not tournament message or that tournament doesn't exist. Contact Vuk.")

    @commands.group(pass_context=True)
    @commands.guild_only()
    async def tournament(self, ctx):
        """Tournament plugin for challonge
        Creating new tournament:
        > tournament create 07-10-2020 20:30 Gold-Plat
        Signing in to tournament:
        > tournament signin <tournament_id>
        Check-in into tournament:
        > tournament checkin <tournament_id>"""
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid sub command passed...')

    @tournament.command()
    @commands.guild_only()
    async def create(self, ctx, date: str, time: str, rank: str):
        """Create tournament event"""
        description = template_description(rank)
        day, month, year = date.split("-")
        hours, minutes = time.split(":")
        rules = config['Sodium']
        try:
            suffix = get_similar_tournaments(rules['url'].format(year, month, day)) + 1
            tourny = challonge.tournaments.create(name=rules['name'],
                                         tournament_type=rules['tournament_type'],
                                         url=rules['url'].format(year, month, day) + "_{}".format(suffix),
                                         description=description,
                                         open_signup=rules['open_signup'],
                                         ranked_by=rules['ranked_by'],
                                         accept_attachments=rules['accept_attachments'],
                                         hide_forum=rules['hide_forum'],
                                         show_rounds=rules['show_rounds'],
                                         private=rules['private'],
                                         notify_users_when_matches_open=rules['notify_users_when_matches_open'],
                                         notify_users_when_the_tournament_ends=rules['notify_users_when_the_tournament_ends'],
                                         sequential_pairings=rules['sequential_pairings'],
                                         start_at=rules['start_at'].format(year, month, day, hours, minutes),
                                         game_id=rules['game_id'],
                                         check_in_duration=rules['check_in_duration']
                                         )
            await ctx.send("Event https://challonge.com/" + rules['url'].format(year, month, day) + "_{} created!".format(suffix))
            t_msg = await ctx.send("React with :white_check_mark: to signin to Sodium Showdown tournament that will take place at {}-{}-{} {}:{} British Time".format(day, month, year, hours, minutes))
            add_new_tournament(tourny["id"], tourny["url"], t_msg.guild.id ,t_msg.channel.id, t_msg.id)


        except Exception as e:
            await ctx.send(e)
            raise

    @tournament.command()
    @commands.guild_only()
    async def destroy(self, ctx, name):
        """Destroy tournament by name"""
        if ctx.message.author.mention == "<@759526413400408126>":
            id = delete_tournament_by_name(name)
            challonge.tournaments.destroy(id)
            await ctx.send("Event {} destroyed.".format(name))
        else:
            await ctx.send("You are not my real mom, {}!".format(ctx.message.author.display_name))

    def get_tournaments(self):
        return [t for t in challonge.tournaments.index()]

    @tournament.command()
    @commands.guild_only()
    async def checkin(self, ctx, tournament_id: str):
        """Check in command"""
        try:
            t_json = self.read_json()
            for tid, event in t_json["tournaments"].items():
                if event.endswith(tournament_id):
                    id = tid
                    tournament_url = event
            name = self.get_player_id_by_name(id, ctx.message.author.display_name)

            url = "https://api.challonge.com/v1"
            path = "/tournaments/{}/participants/{}/check_in.json".format(id, name)
            payload = {"api_key": API_KEY}

            r = requests.post(url + path, params=payload)
            if r.status_code == requests.codes.ok:
                await ctx.send("User {} checked in {} event.".format(ctx.message.author.display_name, tournament_url))
                await ctx.invoke(self.bot.get_command('tournament display'), tournament_id=tournament_id)
            else:
                await ctx.send("Cannot find {} in {} event participant list. Have you signed in?".format(ctx.message.author.display_name, tournament_url))
        except Exception as e:
            await ctx.send(e)
            raise

    def get_player_id_by_name(self, id, name):
        for participant in challonge.participants.index(id):
            if participant["name"] == name:
                return participant["id"]

    @tournament.command()
    @commands.guild_only()
    async def display(self, ctx, tournament_id: str):
        """Displays tournament info"""
        t_json = self.read_json()
        for tid, event in t_json["tournaments"].items():
            if event.endswith(tournament_id):
                id = tid
                tournament_name = event
        self.get_participants(id)
        self.message_id = self.read_json_msg()

        channel = self.bot.get_channel(self.message_id["channel"])

        try:
            self.message_id[tournament_name]
        except KeyError:
            self.message_id[tournament_name] = dict()

        try:
            participants = await channel.fetch_message(self.message_id[tournament_name]["participants"])
        except KeyError:
            participants = await channel.send("Participants placeholder")
            self.message_id[tournament_name]["participants"] = participants.id

        random.seed(a=tournament_name, version=2)

        color = random.randint(0, 15105570)
        p_embed = discord.Embed(title="Participants list", description="Participants list", color=color)
        for player in sorted(self.tournament_dict["participants"]):
            pname = self.tournament_dict["participants"][player][0]
            checked_in = "Checked in: {}".format(str(self.tournament_dict["participants"][player][1]))
            p_embed.add_field(name=pname, value=checked_in, inline=False)
        await participants.edit(content=tournament_name, embed=p_embed)

        self.get_matches(id)
        try:
            completed = await channel.fetch_message(self.message_id[tournament_name]["completed"])
        except KeyError:
            completed = await channel.send("Completed matches placeholder")
            self.message_id[tournament_name]["completed"] = completed.id

        cm_embed = discord.Embed(title="Complete matches", description="Matches list", color=color)
        for mid in sorted(self.tournament_dict["matches"]["complete"]):
            match = self.tournament_dict["matches"]["complete"][mid]
            pname = self.tournament_dict["participants"]
            p1 = pname[match["p1"]][0]
            p2 = pname[match["p2"]][0]
            score = match["score"]
            cm_embed.add_field(name="{} vs. {}".format(p1, p2), value=score, inline=False)
        await completed.edit(content=tournament_name, embed=cm_embed)

        try:
            open = await channel.fetch_message(self.message_id[tournament_name]["open"])
        except KeyError:
            open = await channel.send("Open matches placeholder")
            self.message_id[tournament_name]["open"] = open.id

        om_embed = discord.Embed(title="Open matches", description="Matches list", color=color)
        for mid in sorted(self.tournament_dict["matches"]["open"]):
            match = self.tournament_dict["matches"]["open"][mid]
            pname = self.tournament_dict["participants"]
            p1 = pname[match["p1"]][0]
            p2 = pname[match["p2"]][0]
            om_embed.add_field(name="{} vs. {}".format(p1, p2), value="Match ID: {}".format(mid), inline=False)
        await open.edit(content=tournament_name, embed=om_embed)

        self.save_json_msg(self.message_id)

    def get_participants(self, id):
        self.tournament_dict["participants"] = dict()
        for participant in challonge.participants.index(id):
            pid = participant["id"]
            name = participant["name"]
            checked_in = participant["checked-in"]
            self.tournament_dict["participants"][pid] = [name, checked_in]

    def get_matches(self, id):
        self.tournament_dict["matches"] = dict()
        self.tournament_dict["matches"]["open"] = dict()
        self.tournament_dict["matches"]["complete"] = dict()
        for index, m in enumerate(challonge.matches.index(id), start=1):
            if m["state"] in ["open", "complete"]:
                self.tournament_dict["matches"][m["state"]][m["id"]] = dict()
                self.tournament_dict["matches"][m["state"]][m["id"]]["p1"] = m["player1-id"]
                self.tournament_dict["matches"][m["state"]][m["id"]]["p2"] = m["player2-id"]
                self.tournament_dict["matches"][m["state"]][m["id"]]["score"] = m["scores-csv"]

    @tournament.command()
    @commands.guild_only()
    async def set_channel(self, ctx):
        """Set channel to post tournament data (Vuk only)"""
        if ctx.message.author.mention == "<@759526413400408126>":
            self.message_id = self.read_json_msg()
            channel_id = await ctx.send("Done")
            self.message_id["channel"] = channel_id.channel.id
            self.save_json_msg(self.message_id)
        else:
            await ctx.send("You are not my real mom, {}!".format(ctx.message.author.display_name))

    def read_json(self):
        with open(self.JSON_PATH, "r") as _json_file:
            data = json.load(_json_file)
            return data

    def save_json(self, json_to_save):
        with open(self.JSON_PATH, "w") as _json_file:
            json.dump(json_to_save, _json_file)

    def read_json_msg(self):
        with open(self.JSON_PATH_MSG, "r") as _json_file:
            data = json.load(_json_file)
            return data

    def save_json_msg(self, json_to_save):
        with open(self.JSON_PATH_MSG, "w") as _json_file:
            json.dump(json_to_save, _json_file)
def setup(bot):
    bot.add_cog(SFVTournamentCog(bot))
