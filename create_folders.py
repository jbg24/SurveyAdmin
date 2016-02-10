__author__ = 'jeremyg'

import sys
import pandas as pd
import os
from argparse import ArgumentParser, ArgumentTypeError

'''
This script will take a roster file and clean it, create a clean version, summary file, and restructured file
'''

parser = ArgumentParser()
parser.add_argument('-o', '--outDir', metavar='outDir',
                    help='Parent directory for client folders where panel files, roster info and login'
                         'codes will be saved (default: ./)', required=False)

parser.add_argument('-i', '--inFile', metavar='inFile',
                    help='Profiled schools File to be read in', required=True)

parser.add_argument('-rows', '--rows', metavar='rows',
                    help='Which rows (schools) to make panels for, e.g. 2-5, 7, or A', required=True)


def create_folders(opp_path):
    '''
    Create folders for output
    :param opp_name: (string) opportunity name
    :return:
    '''

    os.makedirs(opp_path)
    os.makedirs(opp_path + "\\Panels")
    os.makedirs(opp_path + "\\RosterData\\Original")
    os.makedirs(opp_path + "\\LoginCodes")

def parseRows(rows):
    '''
    Parse the --rows argument to determine which schools to make panels for
    :param rows: (string) in form 2-5, or 7, or A
    :return: list of rows
    '''

    selection = rows.strip().split(",")

    # Determine which opportunities were selected
    chosen_opps = []

    for nums in selection:
        try:
            if "-" in nums:
                end_values = nums.split("-")
                new_values = range(int(end_values[0]),int(end_values[1])+1)
                chosen_opps.extend(new_values)
            else:
                chosen_opps.append(int(nums))
        except:
             raise ArgumentTypeError("'" + nums + "' is not a range of number. Expected forms like '0-5' or '2'.")

    return chosen_opps


if __name__ == "__main__":

    args = parser.parse_args()

    if not os.path.isfile(args.inFile):
        raise IOError('The profiled schools file {} does not exist.'.format(args.cleanList))

    try:
        profiled = pd.read_csv(args.inFile)
    except:
        raise IOError("The profiled schools file {} could not be opened".format(args.inFile))

    if args.rows != 'A':
        row_list = parseRows(args.rows)
        if max(row_list) < len(profiled) and min(row_list)>=0:
            profiled = profiled[profiled.index.isin(row_list)]
        else:
            print >> sys.stderr, ("Row values are out of range - must be from 0 to {}".format(str(len(profiled)-1)))


    # Save in RosterFiles directory if no output directory specified
    if not args.outDir:
        args.outDir = '.'

    for opp in set(profiled['Opportunity'].tolist()):
        outpath = os.path.join(args.outDir,opp)
        if not os.path.exists(outpath):
            create_folders(outpath)


