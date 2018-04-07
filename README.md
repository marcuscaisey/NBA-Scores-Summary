# NBA Scores Summary
![](https://i.imgur.com/tuIGEGq.png)

Script which summarises the NBA games on a given date. Each summary contains the teams' records and the top player of the game (player with highest [gamescore](https://www.nbastuffer.com/analytics101/game-score/)).

## Dependencies
- Beautiful Soup
- requests

Use `pip install -r requirements.txt` to install dependencies.

## Usage
At the command line, type:
```
python NBAScores.py optional-date
```
where optional-date is in dd/mm/yyyy form. If date not given, summary will be for today's date.
