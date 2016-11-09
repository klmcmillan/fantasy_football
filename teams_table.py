import sys
from bs4 import BeautifulSoup
import requests
import sqlite3


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


def load_clubhouse_page(league_id, team_id, season_id):
    """
    Load the team clubhouse page.
    """
    url = 'http://games.espn.com/ffl/clubhouse?leagueId={}&teamId={}&seasonId={}'.format(league_id, team_id, season_id)
    team_soup = BeautifulSoup(requests.get(url).text, 'lxml')

    return team_soup


def parse_teams(team_id, team_soup):
    """
    Parse the following team fields from the clubhouse page (team_soup) for a
    specific team_id:
    (1) division, (2) team name, (3) team acronym, (4) owner and (5) co-owner
    """
    division = team_soup.find('div', {'class': 'games-univ-mod1'}).text

    team = team_soup.find('h3', {'class': 'team-name'}).text
    team_name = team.split('(')[0].strip()
    team_acronym = team.split('(')[1].replace(')', '')

    managers = team_soup.find_all('li', {'class': 'per-info'})
    if len(managers) > 1:
        owner = managers[0].get_text()
        co_owner = managers[1].get_text().split('|')[1].strip()
    else:
        owner = managers[0].get_text()
        co_owner = None

    teams = {'team_id': team_id, 'team_abbr': team_acronym,
             'team_name': team_name, 'division': division, 'owner': owner,
             'co_owner': co_owner}

    return teams


def write_teams_to_db(ff_db, teams):
    """
    Write team data to database.
    """
    print '\nOpening fantasy football database ...'

    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    cur.execute('''

    CREATE TABLE IF NOT EXISTS Teams (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        team_id INTEGER UNIQUE,
        team_abbr TEXT,
        team_name TEXT,
        division TEXT,
        owner TEXT,
        co_owner TEXT
    );
    ''')

    print 'Writing team data to database ...'

    cur.execute('''INSERT OR REPLACE INTO Teams
        (team_id, team_abbr, team_name, division, owner, co_owner)
        VALUES ( ?, ?, ?, ?, ?, ? )''',
        ( teams['team_id'], teams['team_abbr'], teams['team_name'],
          teams['division'], teams['owner'], teams['co_owner'] ) )

    conn.commit()

    print 'Team data written to database!\n'

    conn.close()


def main():
    """
    User-specified parameters:
    (1) ff_db: name of database to save player data to
    (2) league_id: id number of the ESPN FF league
    (3) season_id: year of FF season

    Returns:
    Writes to ff_db all team owner information.
    """
    ff_db = 'DATABASE_NAME.sqlite'
    league_id = 000000
    season_id = 0000

    num_teams = get_num_teams(league_id, season_id)
    team_ids = range(1, num_teams+1)

    for team_id in team_ids:
        team_soup = load_clubhouse_page(league_id, team_id, season_id)
        teams = parse_teams(team_id, team_soup)
        write_teams_to_db(ff_db, teams)


if __name__ == '__main__':
    main()
    sys.exit(0)
