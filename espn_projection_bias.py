import sys
import os
import numpy as np
import numpy.random as npr
import pandas as pd
import sqlite3
import scipy as sp
import scipy.stats
from matplotlib import pylab as plt


def get_relative_errors(ff_db, position_filter=None, slot_filter=None):
    """
    Calculate the relative projection error for all relevent player scores saved
    in ff_db. Set position_filter to a specific position (e.g. 'WR', 'RB', etc.)
    to get errors for that position only. Default is to get errors for all
    positions. Set slot_filter to 'Bench' to get errors only for starters.
    Default is to get errors for starters and bench players.
    """
    conn = sqlite3.connect(ff_db)
    cur = conn.cursor()

    sqlstr = '''SELECT Players.slot, Players.position, Players.projected_points,
        Players.actual_points FROM Players'''
    players = pd.read_sql_query(sqlstr, conn)

    players['error'] = (players['projected_points'] - players['actual_points']) / players['projected_points']

    # eliminate BYE week and injured players from analysis
    players = players.ix[players['projected_points']!=0, :].reset_index(drop=True)

    if position_filter is not None:
        players = players.ix[players['position']==position_filter, :].reset_index(drop=True)

    if slot_filter is not None:
        players = players.ix[players['slot']!=slot_filter, :].reset_index(drop=True)

    errors = players['error'].values

    return errors


def bootstrap(data, num_samples, statistic, alpha):
    """
    Implementation of bootstrap sampling that returns the following:
    (1) Distiubution of statistic
    (2) Mean statisitic
    (3) 100.0*(1-alpha) CI for statistic (low)
    (4) 100.0*(1-alpha) CI for statistic (high)
    """
    n = len(data)
    idx = npr.randint(0, n, (num_samples, n))
    samples = data[idx]
    stat = np.sort(statistic(samples, 1))

    return stat, np.mean(stat), stat[int((alpha/2.0)*num_samples)], stat[int((1-alpha/2.0)*num_samples)]


def main():
    """
    User-specified parameters:
    (1) ff_db: name of database to extract data from
    (2) position_filter: filters data by position
    (3) slot_filter: filters data by starter/bench designation

    Returns:
    (1) Creates 'figures' directory in current working directory (if it doesn't
        already exist)
    (2) Generates a figure that contains subplots with the following
        information: (a) distribution of realtive errors, (b) distribution of
        mean realtive errors (bootstrapped) with 95% CI and (c) distribution of
        median relative errors (bootstrapped) with 95% CI
    """
    ff_db = 'DATABASE_NAME.sqlite'
    position_filter=None
    slot_filter=None

    errors = get_relative_errors(ff_db, position_filter, slot_filter)
    dist_mean, m_mean, ci_low_mean, ci_high_mean = bootstrap(errors, 10000, np.mean, 0.05)
    dist_median, m_median, ci_low_median, ci_high_median = bootstrap(errors, 10000, np.median, 0.05)

    fig, ax = plt.subplots(nrows=1, ncols=3, facecolor='white')
    fig.tight_layout()

    # relative errors
    binwidth = 2*scipy.stats.iqr(errors)*len(errors)**(-1./3)
    ax[0].hist(errors, bins=np.arange(min(errors), max(errors) + binwidth, binwidth))
    ax[0].tick_params(axis='x', labelsize=10)
    ax[0].set_xlabel('Relative error', fontsize=10)

    # bootstrapped mean relative error
    binwidth = 2*scipy.stats.iqr(dist_mean)*len(dist_mean)**(-1./3)
    ax[1].hist(dist_mean, bins=np.arange(min(dist_mean), max(dist_mean) + binwidth, binwidth))
    ax[1].tick_params(axis='x', labelsize=10)
    ax[1].set_xlabel('Mean relative error (bootstrapped)', fontsize=10)
    ax[1].set_title('95% CI: (' + '{0:.3f}'.format(ci_low_mean) + ', ' + '{0:.3f}'.format(ci_high_mean) + ')', fontsize=10)

    # bootstrapped median relative error
    binwidth = 2*scipy.stats.iqr(dist_mean)*len(dist_mean)**(-1./3)
    ax[2].hist(dist_median, bins=np.arange(min(dist_median), max(dist_median) + binwidth, binwidth))
    ax[2].tick_params(axis='x', labelsize=10)
    ax[2].set_xlabel('Median relative error (bootstrapped)', fontsize=10)
    ax[2].set_title('95% CI: (' + '{0:.3f}'.format(ci_low_median) + ', ' + '{0:.3f}'.format(ci_high_median) + ')', fontsize=10)

    # Make a directory for saving figures if it doesn't already exist
    if not os.path.exists('figures'):
        os.makedirs('figures')

    cwd = os.getcwd()
    fig.savefig(cwd + '/figures/espn_projection_bias.png' ,dpi=300)

    plt.show()


if __name__ == '__main__':
    main()
    sys.exit(0)
