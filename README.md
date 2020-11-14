# Students of Salt Discord Bot

SoS Discord Bot is mainly used to organize Street Fighter V tournaments using https://challonge.com API.
It does not require challonge account for participants - users are registered using their Discord names.

## Usage

### Necessary config
Create config files using provided examples:

#### `bot.ini`:
```ini
[API]
key=EnterTokenHere

[Defaults]
prefix=!?
```

#### `challonge.ini`:
```ini
[API]
name=ChallongeLogin
token=TokenHere

[Sodium]
name=Sodium Showdown!
tournament_type=double elimination
url=sodium_showdown_{}_{}_{}
open_signup=True
ranked_by=match wins
accept_attachments=False
hide_forum=True
show_rounds=False
private=True
notify_users_when_matches_open=False
notify_users_when_the_tournament_ends=False
sequential_pairings=False
start_at={}-{}-{}T{}:{}:00.000+02:00
game_id=183040
check_in_duration=30
```

### Create `db` directory
```sh
mkdir db/
```

### Build Docker image
```sh
docker build -t sos-bot .
```

### Run Docker image
```sh
docker run -v $(pwd)/configs/:/opt/bot/configs/ -v $(pwd)/db/:/opt/bot/db/ sos-bot:latest
```

## Contributing to project
If you want to contribute to this project you can create Pull Request from forked repository.
Make sure to update `CHANGELOG.md` using information provided on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
