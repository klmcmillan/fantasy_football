import sys
from bs4 import BeautifulSoup
import requests
import sqlite3

# Player attributes as parsed from ESPN lineups page
player_attr = {'SLOT': 'slot',
               'PLAYER': 'player',
               'TEAM': 'team',
               'POS': 'position',
               'OPP': 'opponent',
               'STATUS ET': 'game_status',
               'PRK': 'player_rank',
               'PTS': 'points',
               'AVG': 'average_points',
               'LAST': 'last_points',
               'PROJ': 'projected_points',
               'OPRK': 'opponent_rank',
               '%ST': 'percent_start',
               '%OWN': 'percent_own',
               '+/-': 'percent_ownership_change'}


def get_num_teams(league_id, season_id):
    """
    Get the number of teams in the league from the league settings page.
    """
    url = 'http://games.espn.com/ffl/leaguesetup/settings?leagueId={}&seasonId={}'.format(league_id, season_id)
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    table_settings = soup.find_all('table')
    table_settings = table_settings[1]

    rows = table_settings.find_all('tr')
    for row in rows:
        fields = [val.get_text() for val in row.children if len(val.get_text()) > 0]
        if fields[0] == "Number of Teams":
            num_teams = int(fields[1])

    return num_teams


def load_lineup_page(league_id, team_id, week, season_id):
    """
    Load the weekly team lineup page.
    """
    url = 'http://games.espn.com/ffl/clubhouse?leagueId={}&teamId={}&scoringPeriodId={}&seasonId={}'.format(league_id, team_id, week, season_id)
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    table_lineup = soup.find('table', {'class': 'playerTableTable'})

    return table_lineup


def load_scoring_page(league_id, team_id, week, season_id):
    """
    Load the weekly scoreboard data. Specifically, 'QUICK BOX SCORE' data
    loaded. team_id specified so that the data for the team of interest is
    always the first two tables (STARTERS and BENCH) parsed from the webpage.
    """
    url = 'http://games.espn.com/ffl/boxscorequick?leagueId={}&teamId={}&scoringPeriodId={}&seasonId={}&view=scoringperiod&version=quick'.format(league_id, team_id, week, season_id)
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    table_scoring = soup.find_all('table', {'class': 'playerTableTable'}) # returns 4 tables (2 for the team_id and 2 for the opposing team)
    table_scoring = table_scoring[0:2] # table_scoring[0] is the STARTERS table for the team_id and scoring_table[1] is the BENCH table for the team_id

    return table_scoring


def map_player_data(week, team_id, headers, player_raw, player_num):
    """
    Map data parsed from player lineup table to fields listed in player_attr.
    """
    data = {}

    data['week'] = week
    data['team_id'] = team_id

    # Empty slot row
    if len(player_raw) == 11:
        player_raw.insert(2, u' ') # insert for missing OPP field
        player_raw.insert(3, u' ') # insert for missing STATUS ET field
    # BYE week row
    elif len(player_raw) == 12:
        player_raw.insert(3, u' ') # insert for missing STATUS ET field
    # ESPN uses a space instead of an empty string
    player_raw = [None if not val.strip() else val for val in player_raw]

    for header, player_field in zip(headers, player_raw):
        if header == 'PLAYER, TEAM POS':
            # Empty slot
            if player_field == None:
                data[player_attr['PLAYER']] = 'EMPTY-' + str(player_num)
                data[player_attr['TEAM']] = None
                data[player_attr['POS']] = None
            # D/ST
            elif player_field == player_field.split(',')[0]:
                data[player_attr['PLAYER']] = ' '.join(player_field.split()[:2])
                data[player_attr['TEAM']] = None
                data[player_attr['POS']] = player_field.split()[2]
            # Positions other than D/ST
            else:
                name = player_field.split(',')[0]
                team_pos = player_field.split(',')[1].strip().split()
                # Dealing with players whose status us 'OUT'
                if name[-1] == '*':
                    data[player_attr['PLAYER']] = name[:-1]
                else:
                    data[player_attr['PLAYER']] = name
                data[player_attr['TEAM']] = team_pos[0]
                data[player_attr['POS']] = team_pos[1]
        else:
            if player_field == '--':
                data[player_attr[header]] = 0
            else:
                data[player_attr[header]] = player_field

    return data


def parse_lineup(week, team_id, table_lineup):
    """
    Parse player data from team lineup tables.
    """
    rows = table_lineup.find_all('tr')
    headers = [val.get_text() for val in rows[1].children if len(val.get_text()) > 0]
    players = []
    player_num = 1 # keep track of slot number to fill in unique player name for empty slots

    for row in rows[2:]:
        if 'pncPlayerRow' in row.attrs['class']:
            player_raw = [val.get_text().replace(u'\xa0', ' ') for val in row.children if len(val.get_text()) > 0]
            players.append(map_player_data(week, team_id, headers, player_raw, player_num))
            player_num += 1
        elif ('playerTableBgRowHead' in row.attrs['class'] or 'playerTableBgRowSubhead' in row.attrs['class']):
            pass

    return players


def parse_scoring(table_scoring):
    """
    Parse player scoring data from team scoreboard tables. If data parsed on a
    week-by-week basis, this data should be the same as the 'last_points' data
    parsed from the weekly team lineups.
    """
    scores = []

    # Starters table
    rows = table_scoring[0].find_all('tr')

    for row in rows[3:]:
        if 'pncPlayerRow' in row.attrs['class']:
            score = [val.get_text().replace(u'\xa0', ' ') for val in row.children if len(val.get_text()) > 0][-1]
            if score == '--': # Empty slot or BYE week
                scores.append(0)
            else:
                scores.append(score)
        elif ('playerTableBgRowHead' in row.attrs['class'] or 'playerTableBgRowSubhead' in row.attrs['class']):
            pass

    # Bench table
    rows = table_scoring[1].find_all('tr')

    for row in rows[2:]:
        if 'pncPlayerRow' in row.attrs['class']:
            score = [val.get_text().replace(u'\xa0', ' ') for val in row.children if len(val.get_text()) > 0][-1]
            if score == '--':
                scores.append(0)
            else:
                scores.append(score)
        elif ('playerTableBgRowHead' in row.attrs['class'] or 'playerTableBgRowSubhead' in row.attrs['class']):
            pass

    return scores


def write_players_to_db(ff_db, players, scores):
    """
    Write player data to database.
    """
    print '\nOpening fantasy football database ...'

    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    cur.execute('''

    CREATE TABLE IF NOT EXISTS Players (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        week INTEGER,
        team_id INTEGER,
        slot TEXT,
        player TEXT,
        team TEXT,
        position TEXT,
        opponent TEXT,
        game_status TEXT,
        player_rank INTEGER,
        points DECIMAL(5,1),
        average_points DECIMAL(5,1),
        last_points DECIMAL(5,1),
        projected_points DECIMAL(5,1),
        actual_points DECIMAL(5,1),
        opponent_rank INTEGER,
        percent_start DECIMAL(5,1),
        percent_own DECIMAL(5,1),
        percent_ownership_change DECIMAL(5,1),
        UNIQUE (week, team_id, slot, player)
    );
    ''')

    print 'Writing player data to database ...'

    for i in range(len(players)):
        # ESPN gives 'rd', 'th', etc. that need to be stripped
        if players[i]['opponent_rank'] != 0:
            players[i]['opponent_rank'] = int(players[i]['opponent_rank'][:-2])
        # Most data was parsed as unicode, so need to convert to numerical data
        players[i]['week'] = int(players[i]['week'])
        players[i]['player_rank'] = int(players[i]['player_rank'])
        players[i]['points'] = float(players[i]['points'])
        players[i]['average_points'] = float(players[i]['average_points'])
        players[i]['last_points'] = float(players[i]['last_points'])
        players[i]['projected_points'] = float(players[i]['projected_points'])
        scores[i] = float(scores[i])
        players[i]['percent_start'] = float(players[i]['percent_start'])
        players[i]['percent_own'] = float(players[i]['percent_own'])
        players[i]['percent_ownership_change'] = float(players[i]['percent_ownership_change'])

        cur.execute('''INSERT OR IGNORE INTO Players
            (week, team_id, slot, player, team, position, opponent, game_status,
            player_rank, points, average_points, last_points, projected_points,
            actual_points, opponent_rank, percent_start, percent_own,
            percent_ownership_change)
            VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''',
            ( players[i]['week'], players[i]['team_id'], players[i]['slot'],
            players[i]['player'], players[i]['team'], players[i]['position'],
            players[i]['opponent'], players[i]['game_status'], players[i]['player_rank'],
            players[i]['points'], players[i]['average_points'], players[i]['last_points'],
            players[i]['projected_points'], scores[i], players[i]['opponent_rank'],
            players[i]['percent_start'], players[i]['percent_own'], players[i]['percent_ownership_change'] ) )

        conn.commit()

    print 'Player data written to database!\n'

    conn.close()


def main():
    """
    User-specified parameters:
    (1) ff_db: name of database to save player data to
    (2) league_id: id number of the ESPN FF league
    (3) season_id: year of FF season
    (4) weeks: list of matchup weeks

    Returns:
    Writes to ff_db all player data from a set of regular season weeks.
    """
    ff_db = 'DATABASE_NAME.sqlite'
    league_id = 000000
    season_id = 0000
    weeks = [1, 2, 3, ...]

    num_teams = get_num_teams(league_id, season_id)
    team_ids = range(1, num_teams+1)

    for week in weeks:
        for team_id in team_ids:
            table_lineup = load_lineup_page(league_id, team_id, week, season_id)
            table_scoring = load_scoring_page(league_id, team_id, week, season_id)
            players = parse_lineup(week, team_id, table_lineup)
            scores = parse_scoring(table_scoring)
            write_players_to_db(ff_db, players, scores)


if __name__ == '__main__':
    main()
    sys.exit(0)
