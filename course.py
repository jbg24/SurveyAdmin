__author__ = 'jeremyg'

from random import random
from bisect import bisect

class Course(object):
    '''
    Course that includes the teacher, specific student IDs, and period when taught.
    Students probabibility of being chosen to survey is based on whether they have been
    chosen for other classes previously. Probability weights are readjusted after
    a student is selected to survey.
    '''

    def __init__(self, course_name, teacherid, teachername, subject, mandatory = False):
        '''
        Constructor accepts list of students, course name, period and whether
        or not the course is a core course.

        :param students: (dictionary) studentID: weight
        :param course_name: (string) name of course
        :param course_period: (string) period when course is offered
        :param course_teacher: (intger) teacher id
        :param core_course: (boolean) indicates whether the course is a core academic course
        :param min_course_perc: (float) minimum percentage of class which needs to be surveyed
        :param max_surveyed_courses: (int) maximum number of courses for which a student can be surveyed
        :return:
        '''

        #variable assignments
        self.student_list = []
        self.students_removed = 0
        self.course_name = course_name
        self.teacher_id = teacherid
        self.teachername = teachername
        self.subject = subject
        self.mandatory = mandatory
        self.closed = False
        self.weight = 1


    #randomly choose student based on weight

    def add(self,studentid):
        self.student_list.append(studentid)

    def get_percentage(self):
        return float(len(self.student_list) - self.students_removed)/len(self.student_list)

    def weighted_choice(self, updated_student_list):
        '''
        :new_student_list (dictionary) students with updated weights
        :return:
        '''

        values = updated_student_list.keys()
        weights = updated_student_list.values()
        total = 0
        cum_weights = []
        for w in weights:
            w = w*100
            total += w
            cum_weights.append(total)

        x = random() * total
        #returns position of value that comes to the right of x
        i = bisect(cum_weights, x)
        self.students_chosen.append(values[i])

        if len(self.students_chosen) == len(self.student_list):
            self.closed = True

        return values[i]

    def reset(self):
        '''
        Reset course to resample
        :return:
        '''
        self.students_chosen = []
        self.closed = False


