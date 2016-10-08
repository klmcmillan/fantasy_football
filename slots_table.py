import sys
from bs4 import BeautifulSoup
import requests
import sqlite3


def load_slot_page(league_id, season_id):
    """
    Load the league settings page. Get table for roster slots.
    """
    url = 'http://games.espn.com/ffl/leaguesetup/settings?leagueId={}&seasonId={}'.format(league_id, season_id)
    soup = BeautifulSoup(requests.get(url).text, 'lxml')
    table_slot = soup.find_all('table')
    table_slot = table_slot[2]

    return table_slot


def parse_slots(table_slot):
    """
    Loop through relevant roster positions and parse position and allowed
    number of starters for that position.
    """
    slots = []

    rows = table_slot.find_all('tr')

    for row in rows[3:10]:
        temp = [val.get_text() for val in row.children if len(val.get_text()) > 0][0:2]
        if temp[0].split('(')[0].strip() == 'Flex':
            position = 'FLEX'
        else:
            position = temp[0].split('(')[1].split(')')[0].replace('/', '')
        slots.append({'position': position, 'slots': int(temp[1])})

    return slots


def write_slots_to_db(ff_db, slots):
    """
    Write slot data to database.
    """
    print '\nOpening fantasy football database ...'

    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    cur.execute('''

    CREATE TABLE IF NOT EXISTS Slots (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        position TEXT,
        slots INTEGER,
        UNIQUE (position, slots)
    );
    ''')

    print 'Writing slot data to database ...'

    for i in range(len(slots)):

        cur.execute('''INSERT OR IGNORE INTO Slots
            (position, slots)
            VALUES ( ?, ? )''',
            ( slots[i]['position'], slots[i]['slots'] ) )

        conn.commit()

    print 'Slot data written to database!\n'

    conn.close()


def main():
    """
    User-specified parameters:
    (1) ff_db: name of database to save slot data to
    (2) league_id: id number of the ESPN FF league
    (3) season_id: year of FF season

    Returns:
    Writes to ff_db the roster settings for the league.
    """
    ff_db = 'DATABASE_NAME.sqlite'
    league_id = 000000
    season_id = 0000

    table_slot = load_slot_page(league_id, season_id)
    slots = parse_slots(table_slot)
    write_slots_to_db(ff_db, slots)


if __name__ == '__main__':
    main()
    sys.exit(0)
