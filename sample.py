'''
Input file with roster data in long format, sample according to max number of classes and any
mandatory courses
'''

import pandas as pd
import os
import sys
from course import Course
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--outDir', metavar='outDir',
                    help='Directory for new sampled restructured data file (default: ./RosterFiles)', required=False)

parser.add_argument('-i', '--inFile', metavar='inFile',
                    help='Restructured roster data file to be read in', required=True)

parser.add_argument('-max', '--max', metavar='max',
                    help='Maximum count of courses for each student', required=True)

parser.add_argument('-keep','--keepFile', metavar = 'keepFile',
                    help='File with list of courses, periods, departments or teachers '
                         'to exclude from sampling', required=False)

def weighted_choice(course_list):
    '''
    Select course based on which couse from the list will have the highest student percentage after one is removed

    :course_list (dictionary) list of course objects
    :return: course object
    '''
    if not course_list:
        print 'here'
    weights = [x.get_whatif_percentage() for x in course_list]
    index = weights.index(max(weights))
    return course_list[index]


def create_courses(roster_data,keep_df=None):
    '''
    Create Course objects by doing one pass of roster file and using info from fields
    StudentID, coursename, TeacherID. Based on the 'keeplist', determine whether a course in mandatry

    Return data frame with new column that contains list of Course objects
    '''

    # Track courses (Course objects) that are created; will eventually be added to main roster dataframe
    course_list = []

    for ix, row in roster_data.iterrows():

        #Info for the course
        sid = row['StudentID']
        course = row['coursename']
        teachID = row['TeacherID']
        subject = row['subject']

        # Does Course already exist
        exists = False
        for course_obj in course_list:
            course_name = course_obj.course_name
            teach_id = course_obj.teacher_id

            if course == course_name and teachID == teach_id:
                course_obj.add(sid)
                course_list.append(course_obj)
                exists = True
                break

        # Continue if course existed
        if exists:
            continue
        else:

            # Check if there is a keep list and, if so, check if this course shoudl be listed as mandatory
            keep = False
            if isinstance(keep_df,pd.DataFrame):
                if course in keep_df['coursename'].tolist() or subject in keep_df['subject'].tolist():
                    keep=True

            # Create new course
            new_course = Course(course,teachID,subject,keep)
            new_course.add(sid)

            course_list.append(new_course)

    roster_data['Course'] = course_list
    return roster_data

def sample_courses(roster_data,max_count,summ_out):
    '''
    Go through roster data which has the course info in column Course to decided which course to remove
    '''

    courses_remove = []

    rost_grouped = roster_data.groupby('StudentID')['Course']
    for sid, courses in rost_grouped:

        # Reset
        max = max_count
        kept = 0
        course_index = {}

        # Course list for each students
        for course,index in zip(courses.tolist(),courses.index.tolist()):
            course_index[course] = index

        # Remove courses that are mandatory and decrement max_count
        for course in course_index.keys():
            if course.mandatory or len(course.student_list)<=5:
                del course_index[course]
                kept += 1
                max -= 1

        if kept >= max_count:
            print >> sys.stdout, "Too many required courses for student {} -- keeping all".format(str(sid))
            continue

        # Sample until at max_count
        while len(course_index.keys()) > max:

            remove_course = weighted_choice(course_index.keys())
            remove_course.students_removed += 1

            courses_remove.append(course_index[remove_course])

            del course_index[remove_course]

    print_summary(roster_data,summ_out)
    return roster_data[-roster_data.index.isin(courses_remove)]

def print_summary(roster_df,out_dir):
    '''
    Print summary of course information to show how many students have been removed from each course.

    Roster_df: dataframe with Course column that includes Course objects
    out_dir: where to output the summary file
    '''
    course_names = []
    teach_ids = []
    percs = []
    course_at_full_count = []
    course_current_count = []

    # Include course info, original number of students, percentage sampled, current number of students
    for course in set(roster_df['Course'].tolist()):
        course_names.append(course.course_name)
        teach_ids.append(course.teacher_id)
        percs.append(course.get_percentage())
        course_at_full_count.append(len(course.student_list))
        course_current_count.append(len(course.student_list) - course.students_removed)

    summary_data = {'Course':course_names,'Teacher': teach_ids, 'Class Size': course_at_full_count, 'Percent Sampled':percs, 'Sampled Size': course_current_count}
    sampling_summary = pd.DataFrame(data=summary_data)

    sampling_summary.to_csv(out_dir,index=False)

def sample(roster_data, out_dir, summ_out,max_count, keep_df=None):
    '''
    Take in a clean roster data file and sample according to a max course count.
    Columns: StudentID, linked_grade, teacherfirst, teacherlast, TeacherID, subject, teachername, coursename
    '''

    cols = roster_data.columns
    roster_data = create_courses(roster_data,keep_df)
    roster_data = sample_courses(roster_data,int(max_count),summ_out)
    roster_data[cols].to_csv(out_dir,index=False)

if __name__ == '__main__':

    args = parser.parse_args()

    # Try opening roster file and if exists read in as df
    if not os.path.isfile(args.inFile):
        raise IOError('The roster file {} does not exist.'.format(args.inFile))

    try:
        roster = pd.read_csv(args.inFile)
    except:
        raise IOError("The roster file {} could not be opened".format(args.inFile))

    # Try opening exclusion file and read in as df
    keep = None
    if args.keepFile:
        if not os.path.isfile(args.keepFile):
            raise IOError('The keep file {} does not exist.'.format(args.inFile))

        try:
            keep = pd.read_csv(args.keepFile)
        except:
            raise IOError("The keep file {} could not be opened".format(args.inFile))

    # Use directory RosterFiles if no output directory specified
    if not args.outDir:
        if not os.path.exists('./RosterFiles'):
            os.makedirs('./RosterFiles')
        args.outDir = './RosterFiles'

    path_noext = os.path.splitext(args.inFile)[0]
    filename = os.path.basename(path_noext)

    print >> sys.stdout, "Sampling " + filename
    sampled_name = filename + '_sampled.csv'
    summ_name = filename + '_samplingSummary.csv'
    sampled_out = os.path.join(args.outDir,sampled_name)
    summ_out = os.path.join(args.outDir,summ_name)

    sample(roster,sampled_out,summ_out,args.max,keep)



