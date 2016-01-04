__author__ = 'jeremyg'
import pandas as pd

def custom_pre_format():
    '''
    Take in clean roster dataframe and perform necessary pre_formatting that will be client-specific
    :param roster_df (dataFrame)
    :return:
    '''

    clean_roster = pd.read_csv("C:\Users\jeremyg\Dropbox (CEP)\YouthTruth\Survey Administration\Panel_Creation_Workspace\Roster\Summit Prep15D_clean.csv")

    clean_roster.groupby(['TeacherID','coursename'])

    teacher = ""
    teacher_list ={}
    to_replace = {}


    for teach_course, students in clean_roster.groupby(['TeacherID','coursename'])['StudentID'].values.iteritems():

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
                        new_course = teach_course[1].split(" ")[:-1]
                        print "Looking at teacher " + str(teach_course[0])
                        print "Combining " + str(key[1]) + " and " + str(teach_course[1]) + " into " + " ".join(new_course)
                        new_teacher_course = (key[0]," ".join(new_course))
                        new_student_list = set(values + students_list)
                        new_keys.append(new_teacher_course)
                        new_values.append(new_student_list)
                        to_remove.append(key)

                        to_replace[key[1]] = new_teacher_course
                        to_replace[teach_course[1]] = new_teacher_course

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


    course_list = clean_roster['coursename'].tolist()

    for index, course in enumerate(course_list):
        if course in to_replace.keys():
            course_list[index] = to_replace[course]

    clean_roster['coursename'] = course_list

    return clean_roster

if __name__ == "__main__":
    test = custom_pre_format()