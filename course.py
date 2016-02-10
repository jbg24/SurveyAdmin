'''
Course object that keeps tracks of course information, students enrolled and whether it's mandatory.
Used when sampling roster data with sample.py
'''

class Course(object):

    def __init__(self, course_name, teacherid, subject, mandatory = False):
        '''
        Constructor accepts information about the course as well as whether it
        cannot be involved in the sampling process (mandatory)

        '''
        #variable assignments
        self.student_list = []
        self.students_removed = 0
        self.course_name = course_name
        self.teacher_id = teacherid
        self.subject = subject
        self.mandatory = mandatory
        self.closed = False

    def add(self,studentid):
        self.student_list.append(studentid)

    def get_percentage(self):
        return float(len(self.student_list) - self.students_removed)/len(self.student_list)

    def get_whatif_percentage(self):
        return float(len(self.student_list) - (self.students_removed+1))/len(self.student_list)

    def reset(self):
        '''
        Reset course to resample
        :return:
        '''
        self.students_chosen = []
        self.closed = False


