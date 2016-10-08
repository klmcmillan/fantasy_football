# fantasy_football

# How this works

## Scraping data

The following files are used to scrape ESPN Fantasy Football league data:

1. matchups_table.py
2. players_table.py
3. slots_table.py
4. teams_table.py

These files can be executed in any order, and each will write data to a user-specified database. Instructions for running these files are described below.

### <a name="matchups"></a>matchups_table.py

First, the following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
```

```ff_db``` is the name of the database to which data will be saved. ```league_id``` is id number of the ESPN Fantasy Football league that is to be scraped. Even if you aren't part of an ESPN Fantasy Football league, you can still use these scripts. Any league that has been set as "open to the public" can be scraped. Just play around with six digit numbers until you find one that works! ```season_id``` is the year of the fantasy football season. This code has been succesffully tested all the way back to the 2012 season. That being said, some data, such as weekly player projections and the scores for players on the bench, can only be parsed for the current season.

After changes to the ```main()``` function are made, simply run the file, and weekly matchup data will be committed to the user-specified database.

### players_table.py

The following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
weeks = [1, 2, 3, ...]
```

```ff_db```, ```league_id``` and ```season_id``` are described [above](#matchups). ```weeks``` is a list of matchup weeks to be scraped. This allows you to scrape data from the league as the season progresses.

After changes to the ```main()``` function are made, run the file, and player data from the matchup weeks of interest will be committed to the user-specified database.

### slots_table.py

The following lines from the ``main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
```

```ff_db```, ```league_id``` and ```season_id``` are described [above](#matchups).

After changes to the ```main()``` function are made, run the file, and roster settings for the league will be committed to the user-specified database.

### teams_table.py

The following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
```

```ff_db```, ```league_id``` and ```season_id``` are described [above](#matchups).

After changes to the ```main()``` function are made, run the file, and team owner information for the league will be committed to the user-specified database.

## Analyzing scores

After a database has been created with league data scraped from the web, the following files can be used to analyze scores from your league:

1. score_analysis.py

Score analysis functions from the proceeding files are described below.

### score_analysis.py

#### make_standings_tables

This function will create the following league standings tables for a given set of matchup weeks:

1. Actual standings
2. Projected standings
3. Best standings

The "actual standings" table is the league standings table based on matchups decided by the actual week-to-week scores. This standings table should match the standings table reported by ESPN. The "projected standings" table is the hypothetical league standings if matchups were decided by the weekly projected scores. The "best standings" table is the hypothetical league standings if matchups were decided by scores based on the optimal combination of players from starters and bench each week. By looking at these different league standings scenarios, you can get a sense of who trusted the projection too much and who left too many points on their bench each week.

#### plot_proj_accuracy

This function will provide a plot of the actual scores vs. the ESPN projected scores for the league for a given set of matchup weeks. An example is provided below. In this example, data points to the left of the unity line indicate that the ESPN projected score is greater than the actual score. Data points to the right of the unity line indicate the actual scores beat the ESPN projections.

![Projection Accuracy](https://github.com/klmcmillan/fantasy_football/blob/master/examples/proj_accuracy_weeks_1-4.png)

#### plot_manager_efficiency

This function will provide a plot of the actual scores vs. best possible scores (optimal combination of players from starters and bench) for the league for a given set of matchup weeks. An example is provided below. In this example, data points closer to the unity line indicate the manager set a more efficient lineup (didn't leave too many points on the bench). Data points further away from the unity line indicate the manager left a lot of points on the bench.

![Manager Efficiency](https://github.com/klmcmillan/fantasy_football/blob/master/examples/manager_efficiency_weeks_1-4.png)

#### plot_absolute_proj_error

This function will provide a bar plot of the absolute difference between the ESPN projected score and actual score for each player from the starting lineup and bench for the league during a given week of matchups. Above each bar is the player's name, postion and a symbol to indicate if they were played as a starter. An example is provided below.

![Absolute Projection Error](https://github.com/klmcmillan/fantasy_football/blob/master/examples/abs_error_week_4.png)

#### plot_relative_proj_error

This function will provide a bar plot of the realative difference between the ESPN projected score and actual score for each player from the starting lineup and bench for the league during a given week of matchups. Above each bar is the player's name, postion and a symbol to indicate if they were played as a starter.

![Relative Projection Error](https://github.com/klmcmillan/fantasy_football/blob/master/examples/rel_error_week_4.png)
