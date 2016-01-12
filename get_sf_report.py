__author__ = 'jeremyg'

from simple_salesforce import Salesforce # To connect to Salesforce API
import pandas as pd
import datetime
import sys
import requests
import os
requests.packages.urllib3.disable_warnings()

def remove_nonascii(text):
    '''
    Remove non-ascii character from text (appears in Salesforce reports occasionaly)
    :param text: String text
    :return: text (string) with the non-ascii characters removed
    '''

    if text:
        return ''.join([i if ord(i) < 128 else '' for i in text])
    else:
        return text

def get_profiled_schools():
    '''
    Get data frame of select values from profiled schools whose survey start dates are greater than TODAY
    :return: (DataFrame)
    '''

    # Connect to salesforce using simple-salesforce
    try:
        sf = Salesforce(username='jeremyg@youthtruthsurvey.org', password='sfcepFr1d2y20',security_token='qqD6p3ncrG64BzYfrFXuA4wA')
    except:
        print "Couldn't connect to Salesforce -- check username, password or token"

    # Query at the Profiled, Organization and Oppurtunity level
    qr = sf.query("SELECT Organization_School__r.Name, Organization_School__r.High_Middle_Elementary__c, Opportunity__r.Name,"
                  "Opportunity__r.Survey_Window__c, School_Survey_Start_Date__c, Short__c,Overall_School_Experience_Report__c,"
                  "Feedback_for_Teachers_Report__c,Early_College_High_School__c,Profiled_Grade_Levels__c,"
                  "Total_of_Students_Currently_Enrolled__c, Project_Based_Learning_Profiled__c, STEM_Profiled__c,"
                  "General_Health_Profiled__c, Drugs_Alcohol_Profiled__c, Learning_Styles_Profiled__c, "
                  "Student_Voice_Leadership_Profiled__c, Student_Motivation_Profiled__c, Emotional_Mental_Health_Profiled__c,"
                  "Nutrition_Exercise_Profiled__c, School_Safety_Profiled__c FROM Profiled__c WHERE School_Survey_Start_Date__c > TODAY "
                  "ORDER BY School_Survey_Start_Date__c")

    # Values of interest
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

    #Iterate through query results
    for record in qr['records']:
        opportunity_list.append(remove_nonascii(record['Opportunity__r']['Name']))
        school_list.append(remove_nonascii(record['Organization_School__r']['Name']))
        survey_windows.append(remove_nonascii(record['Opportunity__r']['Survey_Window__c']))

        datest = record['School_Survey_Start_Date__c']
        datearr = datest.split("-")
        datedt = datetime.date(int(datearr[0]),int(datearr[1]),int(datearr[2]))
        start_dates.append(datedt)

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

    # Clean opportunity list
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
                                     'NutritionExercise':nutriexer, 'DrugAlcohol':drugalcohol, 'EMHealth':emohealth})

    # Retrun DataFrame of profiled schools
    return profiled_schools

def get_report():
    '''
    Get profiled schools from Salesforce API and save as csv
    '''

    # Get Salesforce profiled schools report
    try:
        profiled_schools = get_profiled_schools()
    except:
        "Exiting"
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

    cols.extend(['Retrieved','isMinn','Roster','CombineSection'])

    # Include date and time in DataFrame
    profiled_schools['Retrieved'] = date_time
    profiled_schools['isMinn'] = 0
    profiled_schools['Roster'] = 'TBD'
    profiled_schools['CombineSection'] = 1

    # Thirty days from now to limit results
    thirty_days = datetime.date.today() + datetime.timedelta(45)

    # Either append to existing Profiled School file or create new one
    if os.path.exists('Profiles'):
        try:
            current_profiled = pd.read_csv("Profiles/ProfiledSchools.csv")
            current_profiled = current_profiled[cols]
            profiled_schools = profiled_schools[profiled_schools['Survey Start Date']<thirty_days].append(current_profiled,ignore_index=True)
        except:
            print "\nProfiles/ProfiledSchools.csv Doesn't Exist -- creating new copy"
        try:
            profiled_schools.to_csv("Profiles/ProfiledSchools.csv",cols=cols)
            print "\nUpdated! Profiles/ProfiledSchools.csv\n"
        except IOError:
            print "\n **** Trouble writing to file Profiles/ProfiledSchools.csv ****"
    else:
        os.makedirs('Profiles')
        profiled_schools[profiled_schools['Survey Start Date']<thirty_days].to_csv("Profiles/ProfiledSchools.csv",header=True,cols=cols)
        print "\n Created Profiles Directory and save new copy of ProfiledSchools.csv\n"

def choose_schools():
    try:
        current_profiled = pd.read_csv("Profiles/ProfiledSchools.csv")
        print ""
        print current_profiled[['Opportunity','School_Name']].to_string()
        selection = raw_input("Select the schools (e.g. 5,10-16,20 or A for all:)")
        selection = selection.strip().split(",")

        # Check if all schools were chosen
        if len(selection) == 1 and 'A' in selection:
            return current_profiled
        else:
            chosen_schools = []
            for nums in selection:
                if "-" in nums:
                    end_values = nums.split("-")
                    new_values = range(int(end_values[0]),int(end_values[1])+1)
                    chosen_schools.extend(new_values)
                else:
                    chosen_schools.append(int(nums))
            return current_profiled[current_profiled.index.isin(chosen_schools)]

    except:
        "Profiled Schools Report file does not exist -- run step 1 first to get it from Salesforce"


def main():
    '''
    testing
    :return:
    '''
    #profiled_schools  = get_profiled_schools()
    #profiled_schools.index.names = ['School_Name']
    #thirty_days = datetime.date.today() + datetime.timedelta(45)
    #profiled_schools[profiled_schools['Survey Start Date']<thirty_days].to_csv("test_profiled.csv")

    #for i in qr['records']:

    #    print record['Opportunity__r']['Name'], record['Organization_School__r']['Name'],record['Opportunity__r']['Survey_Window__c'], record['School_Survey_Start_Date__c']
    choose_schools()

if __name__ == "__main__":
    main()