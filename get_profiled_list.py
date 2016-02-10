import simple_salesforce # To connect to Salesforce API
import pandas as pd
import datetime
import sys
import os
from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument('-s', '--startDate',
                    help='From which survey start date profiled schools should be pulled in form YYYY-MM-DD (default: today)', required=False)

parser.add_argument('-o', '--outDir',
                    help='Path where ProfiledSchools.csv will be saved (default: current directory)', required=False)


def remove_nonascii(text):
    '''
    Remove non-ascii character from text (appears in Salesforce reports occasionally)
    :param text: String text
    :return: text (string) with the non-ascii characters removed
    '''

    if text:
        return ''.join([i if ord(i) < 128 else '' for i in text])
    else:
        return text

def get_profiled_schools(start_date):
    '''
    Get data frame of specific values from profiled schools whose survey start dates are greater than TODAY
    :return: (DataFrame)
    '''

    # Connect to salesforce using simple-salesforce
    try:
        print "Connecting to Salesforce API using simple-salesforce..."
        sf = simple_salesforce.Salesforce(username='jeremyg@youthtruthsurvey.org', password='sfcepFr1d2y20',security_token='qqD6p3ncrG64BzYfrFXuA4wA')
    except simple_salesforce.login.SalesforceAuthenticationFailed as e:
        print "Problem connecting to Salesforce API using simple-salesforce"
        print e
        raise

    # Default start_date
    if not start_date:
        start_date = 'TODAY'

    # Query at the Profiled, Organization and Oppurtunity level
    # See SalesforceFields.txt file for listing and description of fields retrieved from Salesforce
    qr_string = ("SELECT State_Profiled__c, Organization_School__r.Name, Organization_School__r.High_Middle_Elementary__c, Opportunity__r.Name,"
                 "Opportunity__r.Survey_Window__c, School_Survey_Start_Date__c, Short__c,Overall_School_Experience_Report__c,"
                 "Feedback_for_Teachers_Report__c,Early_College_High_School__c,Profiled_Grade_Levels__c,"
                 "Total_of_Students_Currently_Enrolled__c, Project_Based_Learning_Profiled__c, STEM_Profiled__c,"
                 "General_Health_Profiled__c, Drugs_Alcohol_Profiled__c, Learning_Styles_Profiled__c, "
                 "Student_Voice_Leadership_Profiled__c, Student_Motivation_Profiled__c, Emotional_Mental_Health_Profiled__c,"
                 "Nutrition_Exercise_Profiled__c, School_Safety_Profiled__c FROM Profiled__c WHERE School_Survey_Start_Date__c > " + start_date +
                 " ORDER BY School_Survey_Start_Date__c")
    try:
        qr = sf.query(qr_string)
    except Exception as e:
        print "Problem with query"
        print e
        raise

    # Values of interest in list form
    opportunity_list = []
    school_list = []
    survey_windows = []
    school_level = []
    school_shorts = []
    start_dates = []
    ose_report = []
    fft_report = []
    early_college = []
    profiled_grade_levels = []
    enrollment = []
    pbl = []
    stem = []
    genhealth = []
    drugalcohol = []
    learnstyle = []
    studentmotiv = []
    studentvoice = []
    emohealth = []
    nutriexer = []
    schlsafety = []
    states = []

    #Iterate through query results and remove non-ascii characters from strings
    for record in qr['records']:
        opportunity_list.append(remove_nonascii(record['Opportunity__r']['Name']))
        school_list.append(remove_nonascii(record['Organization_School__r']['Name']))
        survey_windows.append(remove_nonascii(record['Opportunity__r']['Survey_Window__c']))
        strtdate = str(record['School_Survey_Start_Date__c'])
        strtdate = datetime.datetime.strptime(strtdate,'%Y-%m-%d')
        start_dates.append(strtdate.date())
        school_level.append(remove_nonascii(record['Organization_School__r']['High_Middle_Elementary__c']))
        school_shorts.append(remove_nonascii(record['Short__c']))
        ose_report.append(record['Overall_School_Experience_Report__c'])
        fft_report.append(record['Feedback_for_Teachers_Report__c'])
        early_college.append(record['Early_College_High_School__c'])
        profiled_grade_levels.append(remove_nonascii(record['Profiled_Grade_Levels__c']))
        enrollment.append(record['Total_of_Students_Currently_Enrolled__c'])
        pbl.append(record['Project_Based_Learning_Profiled__c'])
        stem.append(record['STEM_Profiled__c'])
        genhealth.append(record['General_Health_Profiled__c'])
        drugalcohol.append(record['Drugs_Alcohol_Profiled__c'])
        learnstyle.append(record['Learning_Styles_Profiled__c'])
        studentvoice.append(record['Student_Voice_Leadership_Profiled__c'])
        studentmotiv.append(record['Student_Motivation_Profiled__c'])
        emohealth.append(record['Emotional_Mental_Health_Profiled__c'])
        nutriexer.append(record['Nutrition_Exercise_Profiled__c'])
        schlsafety.append(record['School_Safety_Profiled__c'])
        states.append(record['State_Profiled__c'])

    # Clean opportunity list: Remove school year -- needs to be udpated next year - and part info
    clean_opp_list = []
    for opp in opportunity_list:
        opp_name = opp.split("SY 15-16 ")
        if len(opp_name) > 1:
            opp_name = opp_name[1].rsplit(" (")[0]
        else:
            opp_name = opp_name[0]
        clean_opp_list.append(opp_name)

    # Create DataFrame
    profiled_schools = pd.DataFrame({'School_Name':school_list, 'Opportunity': clean_opp_list, 'Survey Window': survey_windows,
                                     'Survey Start Date': start_dates,'School Level':school_level, 'Short': school_shorts,
                                     'OE':ose_report, 'FFT':fft_report,
                                     'EarlyCollege':early_college,"GradeLevels":profiled_grade_levels, "Enrolled":enrollment,
                                     'LearningStyles':learnstyle, 'PBL':pbl, 'STEM':stem, 'StudentVoice':studentvoice,
                                     'StudentMotiv':studentmotiv,'GenHealth':genhealth, 'Safety':schlsafety,
                                     'NutritionExercise':nutriexer, 'DrugsAlcohol':drugalcohol, 'EMHealth':emohealth, 'State':states})

    # Retrun DataFrame of profiled schools
    return profiled_schools

def get_report(start_date,out_dir):
    '''
    Get profiled schools from Salesforce API and save as csv
    '''

    # Get Salesforce profiled schools report
    try:
        profiled_schools = get_profiled_schools(start_date)
    except:
        print " Error: Exiting"
        sys.exit()

    # Switch order of columns
    cols = profiled_schools.columns.tolist()
    cols.insert(0, cols.pop(cols.index('FFT')))
    cols.insert(0, cols.pop(cols.index('OE')))
    cols.insert(0, cols.pop(cols.index('Enrolled')))
    cols.insert(0, cols.pop(cols.index('Short')))
    cols.insert(0, cols.pop(cols.index('School_Name')))
    cols.insert(0, cols.pop(cols.index('Opportunity')))

    # Get current data and time
    curr_date_time = str(datetime.datetime.now())
    date = curr_date_time.rsplit(":",1)[0].split(" ")[0]
    time = curr_date_time.rsplit(":",1)[0].split(" ")[1].split(":")
    time = "".join(time)
    date_time = date + "_" + time

    # Add columns that will indicate when the data was received, whether a school is part of Minnesota, spot for the
    # Roster file and a field to indicate whether a 'Course' and 'Section' will be combined in a roster file (default is
    # 1 which means they will be combined
    cols.extend(['Retrieved','Roster','CombineSection'])

    # Include date and time in DataFrame
    profiled_schools['Retrieved'] = date_time

    # To be filled in if FFT
    profiled_schools['Roster'] = 'TBD'

    # Explained above - default is that 'Course' and 'Section' will be combined
    profiled_schools['CombineSection'] = 1

    # Forty-five days from now to limit results
    fortyfive_days = datetime.date.today() + datetime.timedelta(45)

    # Check if Profiles directory exists and make if not
    if not os.path.exists('SchoolProfiles'):
        os.makedirs('SchoolProfiles')

    if not out_dir:
        out = os.path.join(os.getcwd(),'ProfiledSchools.csv')
    else:
        out = os.path.join(out_dir,'ProfiledSchools.csv')

    # Create new or replace ProfiledSchools.csv file
    try:
        profiled_schools[profiled_schools['Survey Start Date']<fortyfive_days].to_csv(out,header=True,cols=cols)
        print "Saved ProfiledSchools.csv to " + out
    except IOError:
        print "\n **** Trouble writing to file SchoolProfiles/ProfiledSchools.csv ****"
        raise

def main():
    args = parser.parse_args()
    get_report(args.startDate, args.outDir)

if __name__ == "__main__":
    main()
