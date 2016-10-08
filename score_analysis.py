import os
import sys
import math
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import sqlite3
from matplotlib import pylab as plt


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


def get_scores(ff_db, team_id, week):
    """
    Calculate the following scores for a given team_id and week:
    (1) score_proj: Score based on ESPN projections for starters
    (2) score_actual: Score based on actual points for starters
    (3) score_best: Score based on optimal combination of players from starters
                    and bench players
    """
    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    sqlstr = '''SELECT Players.* FROM Players
        WHERE Players.team_id = %s and Players.week = %s''' % (team_id, week)
    players = pd.read_sql_query(sqlstr, conn)

    sqlstr = '''SELECT Slots.* FROM Slots'''
    slots = pd.read_sql_query(sqlstr, conn)

    # Tally projected and real scores for original starters
    idx_starter = np.where(players.loc[:, 'slot'] != 'Bench')[0]
    score_proj = players.loc[idx_starter, 'projected_points'].sum()
    score_proj = float('{0:.1f}'.format(round(score_proj, 1)))
    score_actual = players.loc[idx_starter, 'actual_points'].sum()
    score_actual = float('{0:.1f}'.format(round(score_actual, 1)))

    # Tally best possible score considering optimal lineup
    # QB - will return 0 if no QBs on roster
    num_QB = slots.loc[np.where(slots['position'] == 'QB')[0], 'slots'].values[0]
    idx_QB = np.where(players.loc[:, 'position'] == 'QB')[0]
    score_QB = players.loc[idx_QB, 'actual_points'].sort_values(ascending=False).values[0:num_QB].sum()

    # RB
    num_RB = slots.loc[np.where(slots['position'] == 'RB')[0], 'slots'].values[0]
    idx_RB = np.where(players.loc[:, 'position'] == 'RB')[0]
    score_RB = players.loc[idx_RB, 'actual_points'].sort_values(ascending=False).values[0:num_RB].sum()

    # WR
    num_WR = slots.loc[np.where(slots['position'] == 'WR')[0], 'slots'].values[0]
    idx_WR = np.where(players.loc[:, 'position'] == 'WR')[0]
    score_WR = players.loc[idx_WR, 'actual_points'].sort_values(ascending=False).values[0:num_WR].sum()

    # TE
    num_TE = slots.loc[np.where(slots['position'] == 'TE')[0], 'slots'].values[0]
    idx_TE = np.where(players.loc[:, 'position'] == 'TE')[0]
    score_TE = players.loc[idx_TE, 'actual_points'].sort_values(ascending=False).values[0:num_TE].sum()

    # FLEX (RB, WR or TE) - will return 0 if no players available for FLEX position
    num_FLEX = slots.loc[np.where(slots['position'] == 'FLEX')[0], 'slots'].values[0]
    score_RB_FLEX = np.delete(players.loc[idx_RB, 'actual_points'].sort_values(ascending=False).values, np.arange(0, num_RB))
    score_WR_FLEX = np.delete(players.loc[idx_WR, 'actual_points'].sort_values(ascending=False).values, np.arange(0, num_WR))
    score_TE_FLEX = np.delete(players.loc[idx_TE, 'actual_points'].sort_values(ascending=False).values, np.arange(0, num_TE))
    score_FLEX = np.sort(np.concatenate((score_RB_FLEX, score_WR_FLEX, score_TE_FLEX)))[::-1][0:num_FLEX].sum()

    # D/ST
    num_DST = slots.loc[np.where(slots['position'] == 'DST')[0], 'slots'].values[0]
    idx_DST = np.where(players.loc[:, 'position'] == 'D/ST')[0]
    score_DST = players.loc[idx_DST, 'actual_points'].sort_values(ascending=False).values[0:num_DST].sum()

    # K
    num_K = slots.loc[np.where(slots['position'] == 'K')[0], 'slots'].values[0]
    idx_K = np.where(players.loc[:, 'position'] == 'K')[0]
    score_K = players.loc[idx_K, 'actual_points'].sort_values(ascending=False).values[0:num_K].sum()

    # Sum best scores for each position
    score_best = score_QB + score_RB + score_WR + score_TE + score_FLEX + score_DST + score_K
    score_best = float('{0:.1f}'.format(round(score_best, 1)))

    return score_proj, score_actual, score_best


def make_standings_tables(ff_db, weeks):
    """
    Create league standings using the following scoring methods:
    (1) Score based on ESPN projections (proj_standings)
    (2) Actual score (actual_standings)
    (3) Score based on optimal combination of players from starters and bench
        (best_standings)

    League standings created for a set of team_ids across matchups over a given
    set of weeks.
    """
    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    sqlstr = '''SELECT Matchups.* FROM Matchups'''
    matchups = pd.read_sql_query(sqlstr, conn)

    sqlstr = '''SELECT Teams.team_id, Teams.team_name FROM Teams'''
    teams = pd.read_sql_query(sqlstr, conn)

    # Create copies of teams DataFrame
    proj_standings = teams.copy()
    actual_standings = teams.copy()
    best_standings = teams.copy()

    # Add columns for tallying W/L/T/PCT/PF/PA
    proj_standings['W'] = 0 # nunber of wins
    proj_standings['L'] = 0 # number of losses
    proj_standings['T'] = 0 # number of ties
    proj_standings['PCT'] = 0 # winning percentage
    proj_standings['PF'] = 0 # points for
    proj_standings['PA'] = 0 # points against
    actual_standings['W'] = 0
    actual_standings['L'] = 0
    actual_standings['T'] = 0
    actual_standings['PCT'] = 0
    actual_standings['PF'] = 0
    actual_standings['PA'] = 0
    best_standings['W'] = 0
    best_standings['L'] = 0
    best_standings['T'] = 0
    best_standings['PCT'] = 0
    best_standings['PF'] = 0
    best_standings['PA'] = 0

    for week in weeks:
        # Get matchups for a given week
        idx = np.where(matchups['week'] == week)[0]
        matchups_week = matchups.ix[idx, :].reset_index(drop=True)

        for match in np.arange(np.shape(matchups_week)[0]):
            # Get the team ids for the home and away teams for each matchup
            home_id = teams.loc[np.where(teams['team_name'] == matchups_week.loc[match, 'home'])[0], 'team_id'].values[0]
            away_id = teams.loc[np.where(teams['team_name'] == matchups_week.loc[match, 'away'])[0], 'team_id'].values[0]

            # Get the index corresponding to the home/away team ids
            home_idx = np.where(teams['team_id'] == home_id)[0]
            away_idx = np.where(teams['team_id'] == away_id)[0]

            # Get projected, actual and best possible scores for home/away teams
            score_proj_home, score_actual_home, score_best_home = get_scores(ff_db, home_id, week)
            score_proj_away, score_actual_away, score_best_away = get_scores(ff_db, away_id, week)

            # Projected scores W/L/T
            if score_proj_home > score_proj_away:
                proj_standings.loc[home_idx, 'W'] += 1
                proj_standings.loc[away_idx, 'L'] += 1
            elif score_proj_home < score_proj_away:
                proj_standings.loc[home_idx, 'L'] += 1
                proj_standings.loc[away_idx, 'W'] += 1
            elif score_proj_home == score_proj_away:
                proj_standings.loc[home_idx, 'T'] += 1
                proj_standings.loc[away_idx, 'T'] += 1

            # Projected scores PCT/PF/PA - home
            proj_standings.loc[home_idx, 'PCT'] = float('{0:.2f}'.format(round((proj_standings.loc[home_idx, 'W']+0.5*proj_standings.loc[home_idx, 'T']) / ((proj_standings.loc[home_idx, 'W']+0.5*proj_standings.loc[home_idx, 'T'])+(proj_standings.loc[home_idx, 'L']+0.5*proj_standings.loc[home_idx, 'T'])), 2)))
            proj_standings.loc[home_idx, 'PF'] += score_proj_home
            proj_standings.loc[home_idx, 'PA'] += score_proj_away

            # Projected scores PCT/PF/PA - away
            proj_standings.loc[away_idx, 'PCT'] = float('{0:.2f}'.format(round((proj_standings.loc[away_idx, 'W']+0.5*proj_standings.loc[away_idx, 'T']) / ((proj_standings.loc[away_idx, 'W']+0.5*proj_standings.loc[away_idx, 'T'])+(proj_standings.loc[away_idx, 'L']+0.5*proj_standings.loc[away_idx, 'T'])), 2)))
            proj_standings.loc[away_idx, 'PF'] += score_proj_away
            proj_standings.loc[away_idx, 'PA'] += score_proj_home

            # Actual scores W/L/T
            if score_actual_home > score_actual_away:
                actual_standings.loc[home_idx, 'W'] += 1
                actual_standings.loc[away_idx, 'L'] += 1
            elif score_actual_home < score_actual_away:
                actual_standings.loc[home_idx, 'L'] += 1
                actual_standings.loc[away_idx, 'W'] += 1
            elif score_actual_home == score_actual_away:
                actual_standings.loc[home_idx, 'T'] += 1
                actual_standings.loc[away_idx, 'T'] += 1

            # Actual scores PCT/PF/PA - home
            actual_standings.loc[home_idx, 'PCT'] = float('{0:.2f}'.format(round((actual_standings.loc[home_idx, 'W']+0.5*actual_standings.loc[home_idx, 'T']) / ((actual_standings.loc[home_idx, 'W']+0.5*actual_standings.loc[home_idx, 'T'])+(actual_standings.loc[home_idx, 'L']+0.5*actual_standings.loc[home_idx, 'T'])), 2)))
            actual_standings.loc[home_idx, 'PF'] += score_actual_home
            actual_standings.loc[home_idx, 'PA'] += score_actual_away

            # Actual scores PCT/PF/PA - away
            actual_standings.loc[away_idx, 'PCT'] = float('{0:.2f}'.format(round((actual_standings.loc[away_idx, 'W']+0.5*actual_standings.loc[away_idx, 'T']) / ((actual_standings.loc[away_idx, 'W']+0.5*actual_standings.loc[away_idx, 'T'])+(actual_standings.loc[away_idx, 'L']+0.5*actual_standings.loc[away_idx, 'T'])), 2)))
            actual_standings.loc[away_idx, 'PF'] += score_actual_away
            actual_standings.loc[away_idx, 'PA'] += score_actual_home

            # Best scores W/L/T
            if score_best_home > score_best_away:
                best_standings.loc[home_idx, 'W'] += 1
                best_standings.loc[away_idx, 'L'] += 1
            elif score_best_home < score_best_away:
                best_standings.loc[home_idx, 'L'] += 1
                best_standings.loc[away_idx, 'W'] += 1
            elif score_best_home == score_best_away:
                best_standings.loc[home_idx, 'T'] += 1
                best_standings.loc[away_idx, 'T'] += 1

            # Best scores PCT/PF/PA - home
            best_standings.loc[home_idx, 'PCT'] = float('{0:.2f}'.format(round((best_standings.loc[home_idx, 'W']+0.5*best_standings.loc[home_idx, 'T']) / ((best_standings.loc[home_idx, 'W']+0.5*best_standings.loc[home_idx, 'T'])+(best_standings.loc[home_idx, 'L']+0.5*best_standings.loc[home_idx, 'T'])), 2)))
            best_standings.loc[home_idx, 'PF'] += score_best_home
            best_standings.loc[home_idx, 'PA'] += score_best_away

            # Best scores PCT/PF/PA - away
            best_standings.loc[away_idx, 'PCT'] = float('{0:.2f}'.format(round((best_standings.loc[away_idx, 'W']+0.5*best_standings.loc[away_idx, 'T']) / ((best_standings.loc[away_idx, 'W']+0.5*best_standings.loc[away_idx, 'T'])+(best_standings.loc[away_idx, 'L']+0.5*best_standings.loc[away_idx, 'T'])), 2)))
            best_standings.loc[away_idx, 'PF'] += score_best_away
            best_standings.loc[away_idx, 'PA'] += score_best_home

    # Sort standings by W, PCT, PF and then PA
    proj_standings = proj_standings.sort_values(['W', 'PCT', 'PF', 'PA'], ascending=[False, False, False, False])
    actual_standings = actual_standings.sort_values(['W', 'PCT', 'PF', 'PA'], ascending=[False, False, False, False])
    best_standings = best_standings.sort_values(['W', 'PCT', 'PF', 'PA'], ascending=[False, False, False, False])

    return proj_standings, actual_standings, best_standings


def plot_proj_accuracy(ff_db, team_ids, weeks):
    """
    Plot actual scores vs. ESPN projected scores for a set of team_ids and
    weeks. Data points to the left of the unity line indicate that the ESPN
    projected score is greater than the actual score. Data points to the right
    of the unity line indicate the actual scores beat the ESPN projections.
    """
    fig = plt.figure()

    scores_proj = []
    scores_actual = []

    for team_id in team_ids:
        for week in weeks:
            score_proj, score_actual, _ = get_scores(ff_db, team_id, week)
            scores_proj.append(score_proj)
            scores_actual.append(score_actual)

    # Find max of all scores and set x- and y-lim to nearest 50 greater than max
    score_max = max(max(scores_proj), max(scores_actual))
    score_lim = int(math.ceil(score_max / 50.0)) * 50

    plt.scatter(scores_actual, scores_proj, c='r', s=80)
    plt.plot([0, score_lim], [0, score_lim], 'k--', linewidth=2.0)

    plt.xlim(0, score_lim)
    plt.ylim(0, score_lim)

    plt.xlabel('Actual score')
    plt.ylabel('ESPN projected score')

    if len(weeks) == 1:
        plt.title('ESPN projection accuracy: Week ' + str(weeks[0]))
    elif len(weeks) > 1:
        plt.title('ESPN projection accuracy: Weeks ' + str(weeks[0]) + '-' + str(weeks[-1]))

    return fig


def plot_manager_efficiency(ff_db, team_ids, weeks):
    """
    Plot actual scores vs. best possible scores for a set of team_ids and weeks.
    Data points closer to the unity line indicate the manager set a more
    efficient lineup (didn't leave too many points on the bench). Data points
    further away from the unity line indicate the manager left a lot of points
    on the bench.
    """
    fig = plt.figure()

    scores_actual = []
    scores_best = []

    for team_id in team_ids:
        for week in weeks:
            _, score_actual, score_best = get_scores(ff_db, team_id, week)
            scores_actual.append(score_actual)
            scores_best.append(score_best)

    # Find max of all scores and set x- and y-lim to nearest 50 greater than max
    score_max = max(max(scores_actual), max(scores_best))
    score_lim = int(math.ceil(score_max / 50.0)) * 50

    plt.scatter(scores_actual, scores_best, c='r', s=80)
    plt.plot([0, score_lim], [0, score_lim], 'k--', linewidth=2.0)

    plt.xlim(0, score_lim)
    plt.ylim(0, score_lim)

    plt.xlabel('Actual score')
    plt.ylabel('Best possible score')

    if len(weeks) == 1:
        plt.title('Manager efficiency: Week ' + str(weeks[0]))
    elif len(weeks) > 1:
        plt.title('Manager efficiency: Weeks ' + str(weeks[0]) + '-' + str(weeks[-1]))

    return fig


def plot_absolute_proj_error(ff_db, week):
    """
    Bar plot of the absolute difference between the ESPN projected score and
    actual score for each player from the starting lineup and bench for a set of
    team_ids during a given week of matchups. Above each bar is the player's
    name, postion and a symbol to indicate if they were played as a starter.
    """
    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    sqlstr = '''SELECT Players.player, Players.position, Players.slot,
        Players.projected_points, Players.actual_points
        FROM Players WHERE Players.week = %s''' % (week)
    df = pd.read_sql_query(sqlstr, conn)

    # Only consider players with projections > 0
    idx = np.where(df.loc[:, 'projected_points'] > 0)[0]
    df = df.ix[idx, :].reset_index(drop=True)

    df['abs_error'] = df['projected_points']-df['actual_points']
    df = df.sort_values(['abs_error'], ascending=[False]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(40,20))

    errors_pos = []
    errors_neg = []

    for idx, player, position, slot, abs_error in zip(df.index.values, df['player'], df['position'], df['slot'], df['abs_error']):
        rect = ax.bar(idx, abs_error, width=1)
        # Indicate if player was a starter or not
        if slot != 'Bench':
            label = player + '(' + position + ')' + '*'
        else:
            label = player + '(' + position + ')'
        if rect[0].get_y() >= 0:
            errors_pos.append(rect[0].get_height())
            ax.text(rect[0].get_x() + rect[0].get_width()/2., 1.05*rect[0].get_height(), label, ha='center', va='bottom', rotation='vertical')
        else:
            errors_neg.append(-rect[0].get_height())
            ax.text(rect[0].get_x() + rect[0].get_width()/2., -1.05*rect[0].get_height(), label, ha='center', va='top', rotation='vertical')

    ax.text(3, -3, '* denotes player was started', fontsize=30)
    ax.text(3, -5, '$^1$ error = projected points - actual points', fontsize=30)

    ax.set_xlim(0, np.shape(df)[0])

    # Find max of all positive errors and set positive y-lim to nearest 5 greater than max+5
    # Find min of all negative errors and set negative y-lim to nearest 5 less than min-5
    pos_ylim = int(math.ceil((max(errors_pos)+5) / 5.0)) * 5
    neg_ylim = int(math.floor((min(errors_neg)-5) / 5.0)) * 5
    # Check if neg_ylim greater than the location of text already on plot
    if neg_ylim > -5:
        neg_ylim = -5
    ax.set_ylim(neg_ylim, pos_ylim)

    ax.tick_params(labelsize=30)
    ax.xaxis.set_visible(False)

    ax.set_ylabel('$^1$ESPN projection error (absolute): Week ' + str(week), fontsize=30)

    return fig


def plot_relative_proj_error(ff_db, week):
    """
    Bar plot of the realative difference between the ESPN projected score and
    actual score for each player from the starting lineup and bench for a set of
    team_ids during a given week of matchups. Above each bar is the player's
    name, postion and a symbol to indicate if they were played as a starter.
    """
    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    sqlstr = '''SELECT Players.player, Players.position, Players.slot,
        Players.projected_points, Players.actual_points
        FROM Players WHERE Players.week = %s''' % (week)
    df = pd.read_sql_query(sqlstr, conn)

    # Only consider players with projections > 0
    idx = np.where(df.loc[:, 'projected_points'] > 0)[0]
    df = df.ix[idx, :].reset_index(drop=True)

    df['abs_error'] = (df['projected_points']-df['actual_points']) / df['projected_points']
    df = df.sort_values(['abs_error'], ascending=[False]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(40,20))

    errors_pos = []
    errors_neg = []

    for idx, player, position, slot, abs_error in zip(df.index.values, df['player'], df['position'], df['slot'], df['abs_error']):
        rect = ax.bar(idx, abs_error, width=1)
        # Indicate if player was a starter or not
        if slot != 'Bench':
            label = player + '(' + position + ')' + '*'
        else:
            label = player + '(' + position + ')'
        if rect[0].get_y() >= 0:
            errors_pos.append(rect[0].get_height())
            ax.text(rect[0].get_x() + rect[0].get_width()/2., 1.05*rect[0].get_height(), label, ha='center', va='bottom', rotation='vertical')
        else:
            errors_neg.append(-rect[0].get_height())
            ax.text(rect[0].get_x() + rect[0].get_width()/2., -1.05*rect[0].get_height(), label, ha='center', va='top', rotation='vertical')

    ax.text(3, -0.25, '* denotes player was started', fontsize=30)
    ax.text(3, -0.5, r'$^1$ error = $\mathregular{\frac{projected - actual}{projected}}$', fontsize=30)

    ax.set_xlim(0, np.shape(df)[0])

    # Find max of all positive errors and set positive y-lim to nearest 0.5 greater than max+0.5
    # Find min of all negative errors and set negative y-lim to nearest 0.5 less than min-0.5
    pos_ylim = int(math.ceil((max(errors_pos)+0.5) / 0.5)) * 0.5
    neg_ylim = int(math.floor((min(errors_neg)-0.5) / 0.5)) * 0.5
    # Check if neg_ylim greater than the location of text already on plot
    if neg_ylim > -0.5:
        neg_ylim = -0.5
    ax.set_ylim(neg_ylim, pos_ylim)

    ax.tick_params(labelsize=30)
    ax.xaxis.set_visible(False)

    ax.set_ylabel('$^1$ESPN projection error (relative): Week ' + str(week), fontsize=30)

    return fig


def main():
    """
    User-specified parameters:
    (1) ff_db: name of database to extract data from
    (2) league_id: id number of the ESPN FF league
    (3) season_id: year of FF season
    (4) weeks: list of matchup weeks

    Returns:
    (1) Creates 'figures' directory in current working directory (if it doesn't
        already exist)
    (2) Generates figures from the following functions and saves them to the
        'figures' directory: (a) plot_proj_accuracy, (b) plot_manager_efficiency,
        (c) plot_absolute_proj_error and (d) plot_relative_proj_error
    (3) Creates 'tables' directory in current working directory (if it doesn't
        already exist)
    (4) Generates the following standings tables and saves them to the 'tables'
        directory: (a) proj_standings, (b) actual_standings and (c) best_standings
    """
    ff_db = 'DATABASE_NAME.sqlite'
    league_id = 000000
    season_id = 0000
    weeks = [1, 2, 3, ...]

    # Determine most recent week for list of weeks
    this_week = weeks[-1]

    # Get team_ids for all teams in the league
    num_teams = get_num_teams(league_id, season_id)
    team_ids = range(1, num_teams+1)

    # Get cwd for saving files
    cwd = os.getcwd()

    print '\nGenerating and saving figures...'

    # Make a directory for saving figures if it doesn't already exist
    if not os.path.exists('figures'):
        os.makedirs('figures')

    # Generate figures
    fig_proj_accuracy = plot_proj_accuracy(ff_db, team_ids, weeks)
    fig_manager_efficiency = plot_manager_efficiency(ff_db, team_ids, weeks)
    fig_absolute_proj_error = plot_absolute_proj_error(ff_db, this_week)
    fig_relative_proj_error = plot_relative_proj_error(ff_db, this_week)

    # Increase size of player projection error figures
    fig_absolute_proj_error.set_size_inches(40, 20)
    fig_relative_proj_error.set_size_inches(40, 20)

    # Save figures
    if len(weeks) == 1:
        fig_proj_accuracy.savefig(cwd + '/figures/proj_accuracy_week_' + str(weeks[0]) + '.png', dpi=300, format='png')
        fig_manager_efficiency.savefig(cwd + '/figures/manager_efficiency_week_' + str(weeks[0]) + '.png', dpi=300, format='png')
    elif len(weeks) > 1:
        fig_proj_accuracy.savefig(cwd + '/figures/proj_accuracy_weeks_' + str(weeks[0]) + '-' + str(weeks[-1]) + '.png', dpi=300, format='png')
        fig_manager_efficiency.savefig(cwd + '/figures/manager_efficiency_weeks_' + str(weeks[0]) + '-' + str(weeks[-1]) + '.png', dpi=300, format='png')
    fig_absolute_proj_error.savefig(cwd + '/figures/abs_error_week_' + str(this_week) + '.png', dpi=300, format='png')
    fig_relative_proj_error.savefig(cwd + '/figures/rel_error_week_' + str(this_week) + '.png', dpi=300, format='png')

    print 'Generating and saving tables...\n'

    # Make a directory for saving data tables if it doesn't already exist
    if not os.path.exists('tables'):
        os.makedirs('tables')

    # Create standings tables and save each as a seperate CSV file
    proj_standings, actual_standings, best_standings = make_standings_tables(ff_db, weeks)
    if len(weeks) == 1:
        proj_standings.to_csv(cwd + '/tables/proj_standings_week_' + str(weeks[0]) + '.csv', index=False)
        actual_standings.to_csv(cwd + '/tables/actual_standings_week_' + str(weeks[0]) + '.csv', index=False)
        best_standings.to_csv(cwd + '/tables/best_standings_week_' + str(weeks[0]) + '.csv', index=False)
    elif len(weeks) > 1:
        proj_standings.to_csv(cwd + '/tables/proj_standings_weeks_' + str(weeks[0]) + '-' + str(weeks[-1]) + '.csv', index=False)
        actual_standings.to_csv(cwd + '/tables/actual_standings_weeks_' + str(weeks[0]) + '-' + str(weeks[-1]) + '.csv', index=False)
        best_standings.to_csv(cwd + '/tables/best_standings_weeks_' + str(weeks[0]) + '-' + str(weeks[-1]) + '.csv', index=False)


if __name__ == '__main__':
    main()
    sys.exit(0)
