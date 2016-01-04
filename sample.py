__author__ = 'jeremyg'

import pandas as pd
from course import Course
from random import random
from bisect import bisect


def weighted_choice(course_list,):
    '''
    :new_student_list (dictionary) students with updated weights
    :return:
    '''

    values = course_list
    weights = [x.weight for x in course_list]
    total = 0
    cum_weights = []
    for w in weights:
        w = w*100
        total += w
        cum_weights.append(total)


    # If all below 80%, remove the one that has the highest percentage full
    if total == 0:

        for course in values:
            if course.mandatory == False:
                max = course

        for course in values:
            course.students_removed += 1
            percent_full = course.get_percentage()
            if percent_full > max.get_percentage() and course.mandatory == False:
                max = course
            course.students_removed -= 1
        max.students_removed +=1
        return max

    x = random() * total
    #returns position of value that comes to the right of x
    i = bisect(cum_weights, x)

    if values[i].mandatory:
        values[i].weight = 0
        return None

    # See if you can remove and stay above 80%
    values[i].students_removed += 1
    percent_full = values[i].get_percentage()

    if percent_full < 0.8:
        values[i].students_removed -= 1
        values[i].weight = 0
        return None

    values[i].weight = values[i].weight - 1/(float(len(values[i].student_list)))
    return values[i]

def sample(roster_data, mandatory, max_count, school_short):
    '''
    Parses command-line arguments and creates panel from first argument
	args: (iterable )profiled school file and, if included, argument to indicate that classes with fewer than 5 should not be removed
    '''

    mandatory_list = mandatory
    max_course_count = max_count
    roster_data_columns = roster_data.columns.tolist()

    course_list = []
    student_list = {}

    roster_data['tagged'] = False

    for id, courses in roster_data.iterrows():
        student_list[id] =[]
        course_info = pd.Series(courses).dropna()

        if len(course_info) > ((max_course_count*6) + 1):
            roster_data.ix[id, 'tagged'] = True

        courses_only = course_info.index.tolist()[5::6]
        teachers_only = course_info.index.tolist()[2::6]
        teachernames_only = course_info.index.tolist()[4::6]
        subjects_only = course_info.index.tolist()[3::6]

        for teacher, course, teachername, subject in zip(teachers_only,courses_only,teachernames_only, subjects_only):
            mandatory = False
            if courses[subject] in mandatory_list:
                mandatory = True

            course_combo = (courses[teacher],courses[course], courses[teachername], courses[subject])

            added = False

            for existing_course in course_list:
                existing_combo = (existing_course.teacher_id, existing_course.course_name, existing_course.teachername, existing_course.subject)
                if course_combo == existing_combo:
                    existing_course.add(id)
                    student_list[id].append(existing_course)
                    added = True

            if added == False:
                new_course = Course(course_combo[1],course_combo[0],course_combo[2], course_combo[3],mandatory)
                new_course.add(id)
                student_list[id].append(new_course)
                course_list.append(new_course)



    flagged_students = roster_data[roster_data['tagged'] == True]
    flagged_students.to_csv("testing_before.csv",index=True)
    flagged_ids = flagged_students.index.tolist()
    student_list_test = student_list

    for student in flagged_ids:
        courses_over = len(student_list_test[student]) - max_course_count

        for i in range(courses_over):
            removed = True
            while (removed):
                removed_course = weighted_choice(student_list_test[student])
                if removed_course:
                    student_list_test[student].remove(removed_course)
                    removed = False


    course_names = []
    course_teachers = []
    course_at_full_count =[]
    course_percentage =[]
    course_current_count = []


    print "\n"
    for each_course in course_list:
        course_names.append(each_course.course_name)
        course_at_full_count.append(len(each_course.student_list))
        if each_course.get_percentage() < 0.8:
            print "Going below 80% for: " + each_course.teachername + ", " + each_course.course_name + " (" + str(each_course.get_percentage()) + ")"
        course_teachers.append(each_course.teachername)
        course_percentage.append(each_course.get_percentage())
        course_current_count.append(len(each_course.student_list) - each_course.students_removed)
    print "\n"

    summary_data = {'Course':course_names, 'Class Size': course_at_full_count, 'Percent Sampled':course_percentage, 'Sampled Size': course_current_count, 'Teacher': course_teachers}
    sampling_summary = pd.DataFrame(data=summary_data)


    sampling_summary.to_csv("Roster/" + school_short + "sampling_summary.csv", header=True,index=False)


    line_value = []
    finish_column = roster_data_columns[(max_course_count*6)-1]
    final_roster = roster_data.ix[:,:finish_column]
    for student in student_list_test.keys():
        for each_course in student_list_test[student]:
            line_value.extend([each_course.teachername.split(" ")[0],each_course.teachername.split(" ")[1], each_course.teacher_id, each_course.subject, each_course.teachername, each_course.course_name])
        final_roster.ix[student] = line_value
        line_value = []
    final_roster['StudentID'] = final_roster.index
    final_roster = final_roster.reset_index(drop=True)
    return final_roster



