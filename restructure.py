__author__ = 'jeremyg'

import pandas as pd
import subprocess
import os
import argparse

'''
Restructure data file from long to wide - currently done using a STATA do file
'''

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--outDir', metavar='outDir',
                    help='Directory for files to be output to (default: ./RosterFiles)', required=False)

parser.add_argument('-i', '--inFile', nargs = '+',
                    help='File[s] to be read in', required=True)

def dostata(dofile, *params):
    '''
    Launch a do-file, given the fullpath to the do-file
    and a list of parameters.
    '''

    cmd = ["stata-64", "/e", "do", dofile]

    #parameters that act as arguments for the stata do file
    for param in params:
        cmd.append(param)
    return subprocess.call(cmd)

def restructure(input_path,output_path):
    '''
    Restructure roster file from long to wide

    :param roster_df: (DataFrame) roster file with the following headers: StudentID,linked_grade,teacherfirst,
                                  teacherlast,TeacherID,subject,teachername,coursename
    :return: restructured roster DataFrame
    '''

    dostata("Stata/restructure.do", input_path, output_path)

if __name__ == '__main__':

    args = parser.parse_args()

    # Save in RosterFiles directory if no output directory specified
    if not args.outDir:
        if not os.path.exists('./RosterFiles'):
            os.makedirs('./RosterFiles')
        args.outDir = './RosterFiles'

    for roster in args.inFile:

        if not os.path.isfile(roster):
            raise IOError('The roster file {} does not exist.'.format(roster))

        try:
            open_test = open(roster, "r")
            open_test.close()
        except IOError:
            raise IOError("The roster file {} could not be opened".format(roster))

        # Output path
        path_noext = os.path.splitext(roster)[0]
        filename = os.path.basename(path_noext)
        restruct_name = filename + '_restructured.csv'
        restruct_name = os.path.join(args.outDir,restruct_name)

        # Restructure
        restructure(roster,restruct_name)

