import re
import sys
import datetime

from bs4 import BeautifulSoup
import requests

URL = 'http://www.basketball-reference.com'
COUNTING_STATS = {'fg', 'fga', 'fg3', 'fg3a', 'ft', 'fta', 'orb', 'drb', 'ast',
                  'stl', 'blk', 'tov', 'pf', 'pts'}
SUMMARY_WIDTH = 61


class Game:
    def __init__(self, url):
        self.teams = self._get_teams(url)

    def _get_teams(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        box_scores = soup.find_all('div', id=re.compile(r'all_box_\w+_basic'))
        return [Team(box_score) for box_score in box_scores]

    def __repr__(self):
        return '{road_team} {road_score} - {home_score} {home_team}'.format(
            road_team=self.teams[0],
            road_score=self.teams[0].score,
            home_team=self.teams[1],
            home_score=self.teams[1].score)


class Team:
    def __init__(self, box_score):
        self.name = re.search(r'([\w ]+) ', box_score.h2.string).group(1)
        self.acronym = re.search(r'x_(\w+)_', box_score['id']).group(1).upper()
        self.record = re.search(r'\((\d+-\d+)', box_score.h2.string).group(1)
        self.players = self._get_players(box_score)
        self.totals = self._get_totals(box_score)

    def _get_players(self, box_score):
        attrs = {'data-stat': 'player', 'scope': 'row'}
        rows = [th.parent for th in box_score.find_all('th', attrs=attrs)
                if th.parent.td['data-stat'] != 'reason'][:-1]
        return {Player(self, row) for row in rows}

    def _get_totals(self, box_score):
        attrs = {'data-stat': 'player', 'scope': 'row'}
        row = [th.parent for th in box_score.find_all('th', attrs=attrs)][-1]
        tds = row.find_all('td')
        return {td['data-stat']: int(td.string) for td in tds
                if td['data-stat'] in COUNTING_STATS}

    def __repr__(self):
        return self.name

    @property
    def score(self):
        return self.totals['pts']


class Player:
    def __init__(self, team, row):
        self.name = row.a.string
        self.team = team
        self.stats = self._get_stats(row)

    def _get_stats(self, row):
        tds = row.find_all('td')
        return {td['data-stat']: int(td.string) for td in tds
                if td['data-stat'] in COUNTING_STATS}

    def __repr__(self):
        return self.name

    @property
    def game_score(self):
        return (self.stats['pts'] + 0.4 * self.stats['fg'] - self.stats['tov']
                - 0.7 * self.stats['fga'] + 0.7 * self.stats['orb']
                - 0.4 * (self.stats['fta'] - self.stats['ft'])
                + 0.3 * self.stats['drb'] + self.stats['stl']
                + 0.7 * self.stats['ast'] + 0.7 * self.stats['blk']
                - 0.4 * self.stats['pf'])


def print_line(line, left_pad_=None):
    left_pad_ = left_pad(line) if left_pad_ is None else left_pad_
    right_pad = SUMMARY_WIDTH - left_pad_ - len(line)
    print('*' + left_pad_ * ' ' + line + right_pad * ' ' + '*')


def left_pad(line, width=None):
    width = SUMMARY_WIDTH if width is None else width
    return (width - len(line)) // 2


def summarise_game(game):
    print_line('')

    # Team's names
    road_team = game.teams[0]
    home_team = game.teams[1]
    team_names = '{}   @   {}'.format(road_team.name, home_team.name)
    print_line(team_names)

    # Team's scores
    road_score_pad = left_pad(str(road_team.score), len(road_team.name))
    home_score_pad = left_pad(str(home_team.score), len(home_team.name))
    centre_pad = (len(road_team.name) - len(str(road_team.score))
                  - road_score_pad + 7 + home_score_pad)
    scores = str(road_team.score) + centre_pad * ' ' + str(home_team.score)
    print_line(scores, left_pad(team_names) + road_score_pad)

    # Team's records
    road_record_pad = left_pad(road_team.record, len(road_team.name))
    home_record_pad = left_pad(home_team.record, len(home_team.name))
    centre_pad = (len(road_team.name) - len(road_team.record)
                  - road_record_pad + 7 + home_record_pad)
    records = road_team.record + centre_pad * ' ' + home_team.record
    print_line(records, left_pad(team_names) + road_record_pad)

    print_line('')

    # Top player's name
    players = [player for team in game.teams for player in team.players]
    top_player = max(players, key=lambda x: x.game_score)
    top_player_name = 'Top Player - {name} ({team})'.format(
        name=top_player.name,
        team=top_player.team.acronym)
    print_line(top_player_name)

    # Top player's stats
    stats = '{pts} PTS, {reb} REB, {ast} AST, {stl} STL, {blk} BLK'.format(
        pts=top_player.stats['pts'],
        reb=top_player.stats['orb'] + top_player.stats['drb'],
        ast=top_player.stats['ast'],
        stl=top_player.stats['stl'],
        blk=top_player.stats['blk'])
    print_line(stats)

    print_line('')
    print('*' * (SUMMARY_WIDTH + 2))


def summarise_games(date):
    match = re.match(r'(\d+)/(\d+)/(\d+)', date)
    params = {
        'day': match.group(1),
        'month': match.group(2),
        'year': match.group(3),
    }
    response = requests.get(URL + '/boxscores', params=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    link_tds = soup.find_all('td', class_='gamelink')
    game_urls = [URL + td.a['href'] for td in link_tds]

    # Title and date
    print_line('*' * SUMMARY_WIDTH)
    print_line('')
    print_line('NBA Scores Summary')
    print_line(date)
    print_line('')
    print_line('*' * SUMMARY_WIDTH)

    for url in game_urls:
        game = Game(url)
        summarise_game(game)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        date = sys.argv[1]
    else:
        date = datetime.datetime.strftime(datetime.datetime.now(), '%d/%m/%Y')
    summarise_games(date)
