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

```ff_db``` is the name of the database to which data will be saved. ```league_id``` is the id number of the ESPN Fantasy Football league that is to be scraped. Even if you aren't part of an ESPN Fantasy Football league, you can still use these scripts. Any league that has been set as "open to the public" can be scraped. Just play around with six digit numbers until you find one that works! ```season_id``` is the year of the fantasy football season. This code has been succesffully tested all the way back to the 2012 season. That being said, some data, such as weekly player projections and the scores for players on the bench, can only be parsed for the current season.

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

The following lines from the ```main()``` function need to be changed:

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
2. espn_projection_bias.py

Usage instructions and descriptions of functions from the preceeding files are provided below.

### score_analysis.py

In order to use the file as is, the following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
league_id = 000000
season_id = 0000
weeks = [1, 2, 3, ...]
```

```ff_db``` is the name of the database from which data will be read. ```league_id``` is the id number of the ESPN Fantasy Football league. ```season_id``` is the year of the fantasy football season. ```weeks``` is a list of matchup weeks from which scores are to be analyzed. 

After changes to the ```main()``` function are made, simply run the file, and a set of images and spreadsheets will be generated.

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

### espn_projection_bias.py

A question that usually comes up in fantasy football is "How accurate are the player projections?". Most people rely on these projections to set their lineups, so it's an important question to answer. Since we have scraped the projected and actual scores for each player, we can test if there is any statistically significant bias in the projections (over-projected or under-projected).

The file espn_projection_bias.py was written to help answer the question of bias. The output of the file is a figure that shows the following: (1) distribution of relative projection errors, (2) distribution of the mean relative projection errors and (3) distriubtion of the median realtive projections errors. Distributions of the mean and median relative projection errors are based on bootstrap sampling of the relative projection errors. An efficient bootstrap sampling function is included in this file.

In order to test for statistical significance, 95% confidence intervals are calcualted for the mean and median relative projection errors. In each case, if zero were to fall within the 95% confidence interval, we would say that ESPN’s projections are indistinguishable from zero. If you think fantasy football scoring is normally distributed, you could use the mean as an estimate of the center of the distribution. If you think the scoring may not be normally distributed, you may think the median is a better measure of the center of the distribution. It really depends on how the data is distributed.

The file also includes filters so you can test if there is any statistically significant bias in the projections for specific positions (e.g. 'QB', 'WR', etc.) or in the projections of starters only (defualt is to collectively consider starters and bench players).

In order to use the file as is, the following lines from the ```main()``` function need to be changed:

```python
ff_db = 'DATABASE_NAME.sqlite'
position_filter=None
slot_filter=None
```

```ff_db``` is the name of the database from which data will be read. ```position_filter``` is used to filter the data by position. ```slot_filter``` is used to filter the data by starter/bench designation. If you want to evaulate all player data from your league, keep ```position_filter``` and ```slot_filter``` equal to ```None```. Note that there is already a filter in the code to eliminate players with projected scores of 0 (i.e. injured players of players on a BYE week).

After changes to the ```main()``` function are made, simply run the file, and an image will be generated.

![ESPN Projection Bias](https://github.com/klmcmillan/fantasy_football/blob/master/examples/espn_projection_bias.png)
