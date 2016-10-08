# fantasy_football

# How this works

The following files are used to scrape ESPN Fantasy Football league data:

1. matchups_table.py
2. players_table.py
3. slots_table.py
4. teams_table.py

These files can be executed in any order, and each will write data to a user-specified database. Instructions for running these files are described below.

## matchups_table.py

First, the following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
```

```ff_db``` is the name of the database to which data will be saved. ```league_id``` is id number of the ESPN Fantasy Football league that is to be scraped. Even if you aren't part of an ESPN Fantasy Football league, you can still use these scripts. Any league that has been set as "open to the public" can be scraped. Just play around with six digit numbers until you find one that works! ```season_id``` is the year of the fantasy football season. This code has been succesffully tested all the way back to the 2012 season. That being said, some data, such as weekly player projections and the scores for players on the bench, can only be parsed for the current season.

After changes to the ```main()``` function are made, simply run the file, and weekly matchup data will be committed to the user-specified database.

## players_table.py

The following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
weeks = [1, 2, 3, ...]
```

```ff_db```, ```league_id``` and ```season_id``` are described [above](#matchups_table.py).
