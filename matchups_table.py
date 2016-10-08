from __future__ import division
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


def load_matchup_page(league_id, season_id):
    """
    Load the league schedule page. Get table for regular season matchups only.
    """
    url = 'http://games.espn.com/ffl/schedule?leagueId={}&seasonId={}'.format(league_id, season_id)
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    table_matchup = soup.find_all('table')
    table_matchup = table_matchup[1]

    return table_matchup


def parse_matchups(n_matchups, table_matchup):
    """
    Loop through the number of weekly regular season matchups and parse:
    (1) week of matchup, (2) home team name and (3) away team name.
    """
    matchups = []

    rows = table_matchup.find_all('tr')

    current_week = 1
    match = 0

    for row in rows[2:]:
        temp = []
        for tag in row.find_all():
            try:
                temp.append(tag['title'])
            except KeyError:
                pass
        if len(temp) > 0:
            matchups.append({'week': current_week, 'home': temp[0].split('(')[0].strip(), 'away': temp[1].split('(')[0].strip()})
            match += 1
            if not match%n_matchups:
                current_week += 1

    return matchups


def write_matchups_to_db(ff_db, matchups):
    """
    Write matchup data to database.
    """
    print '\nOpening fantasy football database ...'

    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    cur.executescript('''
    DROP TABLE IF EXISTS Matchups;

    CREATE TABLE Matchups (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        week INTEGER,
        home TEXT,
        away TEXT
    );
    ''')

    print 'Writing matchup data to database ...'

    for i in range(len(matchups)):

        cur.execute('''INSERT INTO Matchups
            (week, home, away)
            VALUES ( ?, ?, ? )''',
            ( int(matchups[i]['week']), matchups[i]['home'], matchups[i]['away'] ) )

        conn.commit()

    print 'Matchup data written to database!\n'

    conn.close()


def main():
    """
    User-specified parameters:
    (1) ff_db: name of database to save matchup data to
    (2) league_id: id number of the ESPN FF league
    (3) season_id: year of FF season

    Returns:
    Writes to ff_db all regular season matchups.
    """
    ff_db = 'DATABASE_NAME.sqlite'
    league_id = 000000
    season_id = 0000

    # Get number of teams in the league and calculate number of weekly matchups
    n_teams = get_num_teams(league_id, season_id)
    n_matchups = n_teams/2

    table_matchup = load_matchup_page(league_id, season_id)
    matchups = parse_matchups(n_matchups, table_matchup)
    write_matchups_to_db(ff_db, matchups)


if __name__ == '__main__':
    main()
    sys.exit(0)
