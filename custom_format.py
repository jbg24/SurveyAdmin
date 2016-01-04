__author__ = 'jeremyg'
# Called from create_panel to create custom formatting of roster data
import pandas as pd
import sys

def custom_pre_format_summit(clean_roster, first_part=True):
    '''
    Take in clean roster dataframe and perform necessary pre_formatting that will be client-specific
    :param roster_df (dataFrame)
    :return:
    '''

    if first_part:
        course_list = clean_roster['class'].tolist()
        for index, course in enumerate(course_list):

            to_replace = " (Mod) "
            to_replace_also = " Mod "
            if to_replace in course:
                course = course.replace(to_replace, " ")
            elif to_replace_also in course:
                course = course.replace(to_replace_also, " ")

            course_list[index] = " ".join(course.split(" ")[:-1])
        clean_roster['class'] = course_list

    if not first_part:
        clean_roster.groupby(['TeacherID','class'])

        teacher = ""
        teacher_list ={}
        to_replace = {}


        for teach_course, students in clean_roster.groupby(['TeacherID','class'])['StudentID'].values.iteritems():

            students_list = students.tolist()

            if teach_course[0] != teacher:
                teacher = teach_course[0]
                teacher_list = {}

            if teacher_list:

                added = False
                new_keys = []
                new_values = []
                to_remove = []
                for key, values in teacher_list.iteritems():


                    for student in students_list:
                        compared_course = key[1]

                        current_course_split = teach_course[1].split(" ")
                        compared_course_split = compared_course.split(" ")

                        if student in values and compared_course_split[0:2] == current_course_split[0:2]:
                            new_course = teach_course[1].rsplit(" - ",1)[:-1]
                            print "\n"
                            print "Looking at teacher " + str(teach_course[0])
                            print "Combining " + str(key[1]) + " and " + str(teach_course[1]) + " into " + " ".join(new_course)
                            new_teacher_course = (key[0]," ".join(new_course))
                            new_student_list = set(values + students_list)
                            new_keys.append(new_teacher_course)
                            new_values.append(new_student_list)
                            to_remove.append(key)

                            to_replace[key[1]] = new_teacher_course[1]
                            to_replace[teach_course[1]] = new_teacher_course[1]

                            added = True
                            break

                if not added:
                    teacher_list[teach_course] = students_list
                else:
                    for removal in to_remove:
                        teacher_list.pop(removal)
                    for key, value in zip(new_keys, new_values):
                        teacher_list[key] = list(value)


            else:
                teacher_list[teach_course] = students_list


        course_list = clean_roster['class'].tolist()

        for index, course in enumerate(course_list):
            if course in to_replace.keys():
                course_list[index] = to_replace[course]

        clean_roster['class'] = course_list

        # Check for duplicates in studentID, teacherid, course, period
        length_pre = len(clean_roster)

        # Check for duplicates
        clean_roster = clean_roster.drop_duplicates(cols=['StudentID', 'TeacherID', 'class'], take_last=True)

        length_dedup = len(clean_roster)

        # Removed duplicates from roster but doesn't need to abort
        if length_dedup != length_pre:
            print "Removed %d duplicate values from roster data" % (length_pre - length_dedup)

    return clean_roster


def part_three(df):
    '''
        - if same teacher, same course, two periods, remove period 1(E) or 2(E)
    :param df:
    :return: indeces to remove
    '''

    index_drop = []

    # Iterate through each students courses
    for student, course_info in df.sort(['TeacherID','class']).groupby("StudentID"):

        # Keep track of first index, course, and teacher id
        start=True
        prev_index = -1
        prev_course = ""
        prev_teachid = ""

        # Iterate throug each course and teacher
        for index, course in course_info['class'].iteritems():
            # Starting
            if start:
                prev_index = index
                prev_course  = course
                prev_teachid = course_info.ix[index]['TeacherID']
                start = False
            else:
                if (course == prev_course) and (course_info.ix[index]['TeacherID'] == prev_teachid):
                    if course_info.ix[prev_index]['period'] == "1(E)" or course_info.ix[prev_index]['period'] == "2(E)":
                        index_drop.append(prev_index)
                    else:
                        index_drop.append(index)

                    print "Multiple periods found for the same teacher/course: "
                    print student, course_info
                    print "\n"
                prev_course = course
                prev_teachid = course_info.ix[index]['TeacherID']
                prev_index = index

    print "Dropping the following"
    print df[df.index.map(lambda x: x in index_drop)]
    print "\n"

    return df[df.index.map(lambda x: x not in index_drop)]

def part_two(df):
    '''
        - remove Creative Writing if student has same teacher for English and Creative Writing and more than 4 courses

    :param df:
    :return:
    '''
    index_drop = []

    # Iterate through each students courses
    for student, course_info in df.sort(['TeacherID','class']).groupby("StudentID"):

        # Keep track of first index, course, and teacher id
        start=True
        prev_index = -1
        prev_course = ""
        prev_teachid = ""

        if len(course_info) > 4:

            # Iterate throug each course and teacher
            for index, course in course_info['class'].iteritems():
                # Starting
                if start:
                    prev_index = index
                    prev_course  = course
                    prev_teachid = course_info.ix[index]['TeacherID']
                    start = False
                else:
                    curr_course_split = course.split(" ")
                    prev_course_split = prev_course.split(" ")
                    curr_teach = course_info.ix[index]['TeacherID']

                    if curr_teach == prev_teachid and "Creative" in prev_course_split and "Writing" in prev_course_split and "English" in curr_course_split:
                        index_drop.append(prev_index)

                        print "Creative Writing and English found for"
                        print student, course_info
                        print "\n"

                    prev_course = course
                    prev_teachid = course_info.ix[index]['TeacherID']
                    prev_index = index

    print "Dropping the following"
    print df[df.index.map(lambda x: x in index_drop)]
    print "\n"

    return df[df.index.map(lambda x: x not in index_drop)]

def part_one(df):
    '''
        - combine honors and non-honors classes if same teacher, same period
    :param df: cleaned and updated data frame
    :return:
    '''
    index_drop = []

    # Iterate through each students courses
    for teacher, course_info in df.groupby(['TeacherID','period']):
        course_list = set(course_info['class'].tolist())
        if len(course_list) > 1:
            print "Multiple courses for same period and teacher:"
            print teacher, course_info

            course_list = list(course_list)
            new_course_name = ""
            if course_list[0].split(" ")[0] == course_list[1].split(" ")[0]:
                if len(course_list[0]) < len(course_list[1]):
                    course_new = course_list[0].rstrip()
                    new_course_name = course_new.rsplit(" ",1)[0]
                else:
                    course_new = course_list[1].rstrip()
                    new_course_name = course_new.rsplit(" ",1)[0]
            else:
                new_course_name = course_info['subject'].tolist()[0]

            # SET NEW VALUE
            print "\n Now: "
            for index, course in course_info['class'].iteritems():
                df.set_value(index,"class",new_course_name)

            print df[(df['TeacherID']==teacher[0]) & (df['period']==teacher[1])]
            print "\n"

    return df

def custom_format_hth(df):
    '''
    High Tech High:
    - combine honors and non-honors classes if same teacher, same period
    - remove Creative Writing if student has same teacher for English and Creative Writing
    - if same teacher, same course, two periods, remove period 1(E) or 2(E)
    :param clean_roster: cleaned roster date file (DataFrame)
    :return: custom formatted data (DataFrame)
    '''

    df = part_three(df)
    df = part_two(df)
    df = part_one(df)

    return df

def main(file_path):
    '''
    Read path to csv file which will be imported as data frame and formatted
    :param file_path:
    :return:
    '''

    df = pd.DataFrame.from_csv(file_path,index_col=False)
    roster_headers_new = ['StudentID', 'linked_grade', 'teacherfirst', 'teacherlast', 'TeacherID', 'class', 'section', 'period', 'subject', 'school', 'email']
    df.columns = roster_headers_new

    # *********Remove multiple sections for same course ********** #

    # Indeces to drop
    index_drop = []

    df = part_three(df)
    df = part_two(df)
    df = part_one(df)

    print df

if __name__ == "__main__":
    print sys.argv[1]
    main(sys.argv[1])

