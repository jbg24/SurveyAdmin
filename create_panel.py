### Created to generate panels from Profiled Salesforce file and, if necessary, roster files
### Roster headers should be the following: "Student ID"	"Student's Grade Level"	"Teacher First Name"
###	"Teacher Last Name"	"Teacher ID"	Class Name - Section Number	"Class Period" "Department"	"School Name"	(Teacher's Email is optional)
## TO DO - make sure no ascii characters in panel file 

import sys
import pandas as pd
import numpy as np
#import getopt
import random
import datetime
import re
import subprocess
import string
import ast
import os
#import xlwt
import xlrd
from xlutils.filter import process,XLRDReader,XLWTWriter
#from xlutils.copy import copy
from sample import sample
from upload_panel import upload_panel, upload_survey
from custom_format import custom_format_hth


def dostata(dofile, *params):
    ''' 
    Launch a do-file, given the fullpath to the do-file
    and a list of parameters.
    '''

    cmd = ["C:\Program Files (x86)\Stata12\stata-64.exe", "/e", "do", dofile]
    
    #parameters that act as arguments for the stata do file
    for param in params:
        cmd.append(param)
    return subprocess.call(cmd) 

def check_roster(roster_df,incl_section):
    '''
    Perform a series of checks to make sure the roster data is ok to process

    :param roster_df: data frame of the roster
    :return:
    '''

    # Won't abort until the end if problems are found
    found_problems = False

    # Check for nulls
    if incl_section == False:
        roster_check_nulls = roster_df[['StudentID', 'teacherfirst', 'teacherlast', 'TeacherID', 'class', 'subject']]
    else:
        roster_check_nulls = roster_df

    roster_hasnulls = has_nulls_df(roster_check_nulls)

    if roster_hasnulls:
        print "\nWarning: your roster Data has missing values in rows: " + ", ".join(roster_hasnulls)
        found_problems = True

    # Check for duplicates in studentID, teacherid, course, period
    length_pre = len(roster_df)

    # Check for duplicates
    roster_df = roster_df.drop_duplicates(cols=['StudentID', 'TeacherID', 'subject', 'class', 'period'], take_last=True)

    length_dedup = len(roster_df)

    # Removed duplicates from roster but doesn't need to abort
    if length_dedup != length_pre:
        print "Removed %d duplicate values from roster data" % (length_pre - length_dedup)

    roster_df['teachername'] = roster_df['teacherfirst'] + " " + roster_df['teacherlast']

    # Check each teacher/teacher id combo is 1:1
    roster_grouped_teachname = roster_df.groupby(['teachername'])

    for teachname, otherinfo in roster_grouped_teachname:
        if len(list(otherinfo['TeacherID'].unique())) > 1:
            print " More than one teacher id for name " + teachname
            found_problems = True

    # Per teacherid
    roster_grouped_teachid = roster_df.groupby(['TeacherID'])

    for teachid, otherinfo in roster_grouped_teachid:
        if len(list(otherinfo['teachername'].unique())) > 1:
            print " More than one name for teacher id " + teachid
            found_problems = True

    # Check teacher names, courses, periods and departments for near duplicated based on upper/lower case mistakes
    teacher_firsts = set(roster_df['teacherfirst'].dropna().tolist())
    teacher_lasts = set(roster_df['teacherlast'].dropna().tolist())
    course_list = set(roster_df['class'].dropna().tolist())
    department_list = set(roster_df['subject'].dropna().tolist())

    check_cases = []
    check_cases.extend([teacher_firsts,teacher_lasts,course_list,department_list])
    columns = ['Teacher First Name', 'Teacher Last Name', 'Class', 'Subject']

    for case_list, column in zip(check_cases,columns):
        case_list = list(case_list)
        pre_length = len(case_list)
        all_upper = []
        for item in case_list:
            if item:
                all_upper.append(item.upper())
        post_length = len(set(all_upper))
        if pre_length != post_length:
            print "Discrepency in case for following column: " + column
            found_problems = True

    roster_grouped_teachcourse = roster_df.groupby(['StudentID', 'TeacherID', 'subject', 'class'])

    for studid, otherinfo in roster_grouped_teachcourse:
        if len(list(otherinfo['period'].unique())) > 1:
            print " More than one period for course " + str(studid[3]) + " for student " + str(studid[0])

    #Quit if there were problems with IDs
    if found_problems == True:
        print "Aborting - fix roster data issues before proceeding"
        sys.exit()
    else:
        return roster_df

def has_nulls_df(pd_df):
    '''
    Check to see if a pandas DataFrame has any null values

    pdseries - (pandas Data Frame)
    '''
    
    row_list = []	
    #check for missing values besides School Short which can be auto generated
    if len(pd_df[pd.isnull(pd_df).any(axis=1)]) > 0:
        for rownum in pd_df[pd.isnull(pd_df).any(axis=1)].index:
            row_list.append(str(rownum+2))

    return row_list

def id_generator(size=4):
    '''
    Generate random combination of 1 letter and 3 digits
    '''

    #remove ambiguous o and l characters
    replace_chars = ["o", "l"]
    chars = string.ascii_lowercase

    for char in replace_chars:
        chars = chars.replace(char, "")

    #remove 0
    nums =  string.digits.replace("0","")

    #create code: e.g. b452
    rand_nums = ''.join(random.choice(nums) for _ in range(size-1))
    return random.choice(chars) + rand_nums

def concat_strings(*args):
    ''' 
    Concatenate two strings (args[0] and args[1]) with the third argument (args[2]) indicating whether to put dash
    between the two and single quotes around the second argument
    '''
    
    strs = [str(arg) for arg in args if not pd.isnull(arg)]
    if len(strs) != 3:
        while len(strs) != 3:
            strs.insert(0, "NULL")

    if strs[2] == '0':
        return ' '.join(strs[:-1]) if strs else np.nan
    else: 
        strs[1] = "'" + strs[1] + "'"
        return ' - '.join(strs[:-1]) if strs else np.nan

def process_roster_data(roster_file, school_short, incl_section, output_folder, custom=False):
    '''
    Include proper headers for roster file to prep for stata
    roster_file: string, name of roster file CSV located in current path

    school_short: string, short version of school to be included in final PANEL file name
    incl_section: int, indicates whether we append section to course name (1) or not (0)
    '''
    # Roster headers for clean file
    roster_headers_new = ['StudentID', 'linked_grade', 'teacherfirst', 'teacherlast', 'TeacherID', 'class', 'period', 'subject','schoolname','email']

    # Open roster file
    try:
        roster_df = pd.DataFrame.from_csv(roster_file, index_col =False)
    except:
        print "Problem reading original roster file " + roster_file_path
        sys.exit()

    # Rename columns
    roster_df.columns = roster_headers_new

    roster_df = roster_df[['StudentID', 'linked_grade', 'teacherfirst', 'teacherlast', 'TeacherID', 'class', 'period', 'subject']]

    roster_df = check_roster(roster_df,incl_section)

    # Apply custom formatting
    if custom:
        roster_df = custom_format_hth(roster_df)

    #set up concatenation
    np_concat = np.vectorize(concat_strings)

    #concatenate teacher names
    roster_df['teachername'] = np_concat(roster_df['teacherfirst'], roster_df['teacherlast'], 0)


    #if necessary, concatenate class and period
    if incl_section:
        roster_df['coursename'] = np_concat(roster_df['class'], roster_df['period'], 1)
    else:
        roster_df['coursename'] = roster_df['class']

    #take only pertinent columns
    roster_df = roster_df[['StudentID', 'linked_grade', 'teacherfirst', 'teacherlast', 'TeacherID', 'subject', 'teachername', 'coursename']]

    #output as school_short_clean.csv
    roster_df.to_csv(output_folder + "\\" + school_short + "_clean.csv", header=True, index=False)

def create_roster_files(roster_path,profiled_info,school_short,custom,del_less_five,sampling):

    roster_doc = roster_path + "\\" + profiled_info['Roster']

    incl_section = False
    if profiled_info['CombineSection'] == 1:
        incl_section = True

    # Clean roster data
    process_roster_data(roster_doc, school_short, incl_section,roster_path,custom)

    try:
        summary_restructure = dostata("summarize.do", roster_path + "\\" + school_short + "_clean.csv", roster_path + "\\" + school_short + "_summary.csv")
    except:
        print("Error creating roster summary in stata - check stata log")
        sys.exit()
    # Import clean data
    clean_data = pd.DataFrame.from_csv(roster_path + "\\" + school_short + "_clean.csv", index_col = None)

    # If we are going to remove teachers and classes with fewer than five students
    if del_less_five:

        # Original Roster Count
        length_pre = len(clean_data)

        # Remove IDs where TeacherID, coursename combination only occurs fewer than 5 times
        clean_data = clean_data[clean_data.groupby(['TeacherID', 'coursename'])['StudentID'].transform(len) > 4 ]

        # Roster count after removing small classes
        length_post = len(clean_data)

        print "--- You have removed %d TEACHER/COURSE combination which had <5 students" % (length_pre - length_post)
        # Export new roster file with only teacher/classes with more than 4 students
        clean_data.to_csv("Roster/" + school_short + "_clean_fiveormore.csv", header=True, index=False)

        try:
            summary_restructure = dostata("restructure.do", roster_path + "\\" + school_short + "_clean_fiveormore.csv", roster_path + "\\" + school_short)
        except:
            print("Error restructuring roster data in stata - check stata log")
            sys.exit()

    # Otherwise, use clean.csv file
    else:
        try:
            summary_restructure = dostata("restructure.do", roster_path + "\\" + school_short + "_clean.csv", roster_path + "\\" + school_short + "_restructured.csv")
        except:
            print("Error restructuring roster data in stata - check stata log")
            sys.exit()

    # Read in restructured file for the roster information of the panel
    try:
        roster_part = pd.DataFrame.from_csv(roster_path + "\\" + school_short + "_restructured.csv", index_col = None)
    except:
        print("Couldn't open restructured roster data")
        sys.exit()

    if sampling:
        mandatory_list = ['SPED']
        roster_part_sampling = roster_part.set_index('StudentID')
        roster_part = sample(roster_part_sampling,mandatory_list,4, school_short)

    return roster_part

def make_school_short(short_name,start_date,surv_window):
    '''
    Make school short by appending round info to school 'short' name

    :param short_name: (string) school short name without the round
    :return:
    '''
    year_survey = try_parsing_date(start_date)
    month_survey = str(surv_window).strip()[0]
    if month_survey == 'J' and str(surv_window).strip()[1] == 'a':
        month_survey = 'Ja'
    elif month_survey == 'J':
        month_survey = 'Jn'
    school_short = str(short_name).strip() + year_survey + month_survey
    return school_short

# Parse date to account for different date formatting -- not clear why this happens
def try_parsing_date(text):
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%m/%d/%Y'):
        try:
            dt = datetime.datetime.strptime(text, fmt)
            return dt.strftime('%Y').strip()[-2:]
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def get_ose_info(profiled_info):
    '''
    Get OSE info for the panel and return updated panel DataFrame
    :param panel_df: (DataFrame) panel up to this point
    :param profiled_info: (Series) with profiled information
    :return:
    '''

    #Dictionary that represents all the info for the section of panel that will be the same for each student(OSE part)
    OSE_info = {}

    # Determine grades to be marked in panel
    grade_list = str(profiled_info['GradeLevels']).split(';')

    #put 1's for grade that is included in school
    for grade in grade_list:
        if grade == '3':
            grade = '3rd'
        else:
            grade = grade + 'th'
        OSE_info[grade] = 1

    #set additional topics
    with open('addnl_topics_mapped.csv') as file_object:
        addnl_topics = file_object.read().splitlines()

    for addnl_topic in addnl_topics:
        if addnl_topic == 'School_Name':
            OSE_info[addnl_topic] = profiled_info[addnl_topic]
        elif profiled_info[addnl_topic] == True:
            OSE_info[addnl_topic] = 1
        else:
            OSE_info[addnl_topic] = 0

    # Set MERig
    if OSE_info['FFT'] == True:
        OSE_info['MERig'] = 0
    else:
        OSE_info['MERig'] = 1



    return OSE_info

def get_login_codes(enrollment):
    '''
    Return list of randomly generate login codes in format
    :param num:
    :return:
    '''

    # Checks to make sure won't enter infinite loop, default combinations is 17496 so check at 15000
    if enrollment > 15000:
        print "WARNING: Large number of students (over 15000). Will now terminate"
        sys.exit()

    # Random and unique login codes - use a set
    random_list = set()

    # Create the same number of login codes as the number of enrolled or what we set above as enrollment
    while (len(random_list) < enrollment):
        random_list.add(id_generator())

    return random_list

def get_survey_name_template(profiled_info,is_OSE,is_FFT):
    '''
    Get survey name to upload to qualtrics
    :param profiled_info: (Series) with school info
    :return:
    '''

    is_minn = False
    if 'isMinn' in profiled_info and profiled_info['isMinn'] == 1:
        is_minn = True

    # Determine school level
    level = str(profiled_info['School Level']).strip().split(' ')
    level = level[0][0] + "S"

    survey_template = level + "Mastersurvey"
    if is_minn:
        if level == "HS" or level == "MS":
            survey_template = "SSMastersurvey_MN.qsf"
        else:
            survey_template = "ESMastersurvey_MN.qsf"
    else:
        survey_template = survey_template + ".qsf"

    opp_name = str(profiled_info['Opportunity'])

    school_name = str(profiled_info['Short']).strip()
    survey_type_text = ""
    if is_OSE:
        survey_type_text = "OSE"
    if is_FFT and survey_type_text == "OSE":
        survey_type_text = "OSE/FFT"
    elif is_FFT:
        survey_type_text = "FFT"

    if is_minn:
        if level == 'ES':
            level_name = 'Elementary School'
        else:
            level_name = 'Secondary School'
        survey_name = opp_name + " - 2015-16 State of Minnesota " + level_name  + " Survey - " + school_name
    else:
        survey_name = opp_name + " - 2015-16 " + level + " " + survey_type_text + " Survey - " + school_name

    return level, survey_name, survey_template

def update_response_rates(profiled_info,panel_id,survey_id,level):
    '''
    Get active response rates list and append new info
    :param profiled_info:
    :param panel_id:
    :param survey_id:
    :return:
    '''

    level_dict = {'HS':'year','MS':'m_grade','ES':'e_grade'}
    # Create path for output
    response_rates_file = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..\\..\\ResponseRates\\mainsurveylist.csv'))
    new_info = {}
    new_info['SurveyName'] = profiled_info['School_Name']
    if profiled_info['OE'] == True:
        new_info['OSE'] = 1
    else:
        new_info['OSE'] = 0
    if profiled_info['FFT'] == True:
        new_info['FFT'] = 1
    else:
        new_info['FFT'] = 0
    new_info['SurveyID'] = survey_id
    new_info['PanelID'] = panel_id
    new_info['Enrollment'] = profiled_info['Enrolled']
    new_info['Subgroup'] = level_dict[level]
    if os.path.exists(response_rates_file):
        current_response_list = pd.DataFrame.from_csv(response_rates_file,index_col=None)
        current_response_list = current_response_list.append(new_info,ignore_index=True)
        current_response_list.to_csv(response_rates_file,index=False)
    else:
        output_response = pd.DataFrame(new_info,index=[0])
        output_response.to_csv(response_rates_file,index=False)

def copy2(wb):
    '''
    Patch: add this function to the end of xlutils/copy.py
    :param wb: excel workbook using xlrd
    :return: workbook with format preserved
    '''
    w = XLWTWriter()
    process(
        XLRDReader(wb,'unknown.xls'),
        w
        )
    return w.output[0][1], w.style_list

def print_login_codes(school_name, data_points,codes_path):
    '''
    Using login codes template, print login codes
    :param data_points:
    :param codes_path:
    :return:
    '''

    wbk = xlrd.open_workbook("LoginCodeTemplate.xls", formatting_info=True)
    rdsheet = wbk.sheet_by_index(0)
    wbk_copy,style_list = copy2(wbk)

    sheet_cover = wbk_copy.get_sheet(0)
    xf_index = rdsheet.cell_xf_index(3, 3)
    sheet_cover.write(9,0,school_name + " - Login Codes",style_list[xf_index])

    row_num = 11
    for index, row in data_points.iterrows():
        xf_index = rdsheet.cell_xf_index(2, 2)
        sheet_cover.write(row_num,2,row['StudentID'],style_list[xf_index])
        sheet_cover.write(row_num,4,row['ExternalDataReference'],style_list[xf_index])
        row_num += 1


    sheet_cover.insert_bitmap('YTimage.bmp',0,2)
    wbk_copy.save(codes_path)

def create_panel_from(profile_info, del_less_five = False, upload_p = False, upload_s = False, custom = False, sampling = False,upload=False):
    '''
    Creates panel from profiled salesforce report

    file_obj: Pandas data frame with profiled school info
    del_less_five: (bool) indicates whether to automatically remove classes with fewer than 5 students
    '''

    # Read in panel headers
    with open('PINs_Template_Master.csv') as file_object:
        headers = file_object.read().splitlines()

    # Format date for file name
    date_today = str(datetime.date.today())
    date_today = re.sub('-','',date_today)

    # Create path for output
    output_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..\\ClientFolders'))

    #loop through each profiled school
    for index, row in profile_info.iterrows():

        hasNulls = pd.isnull(row).tolist()
        if True in hasNulls:
            print "\n--Missing Profile Info: Skipping row %i in profiled schools file\n" %(index)
            continue

        is_OSE = row['OE']
        is_FFT = row['FFT']

        # Output panel
        level, survey_name, survey_template = get_survey_name_template(row,is_OSE,is_FFT)
        school_short = make_school_short(row['Short'],row['Survey Start Date'],row['Survey Window'])
        print "Processing %s" %school_short

        output_panel_path = output_path + "\\" + row['Opportunity'] + "\\Panels"
        output_name = level + ' PINs_' + date_today + '_' + school_short + '.csv'
        output_login_path = output_path + "\\" + row['Opportunity'] + "\\LoginCodes"

        if upload == False:
            #create template for panel
            output_panel = pd.DataFrame(columns=headers)

            # Get OSE portion of the panel
            OSE_info = {}
            OSE_info = get_ose_info(row)
            OSE_info['School_Short'] = school_short

            #determine if FFT is included and create class summaries and restructure in stata
            if is_FFT:
                roster_path = output_path + "\\" + row['Opportunity'] + "\\RosterData"
                roster_part = create_roster_files(roster_path,row,OSE_info['School_Short'],custom,del_less_five,sampling)

            # Get login codes
            random_list = set()
            if is_FFT:
                random_list = get_login_codes(len(roster_part))
            else:
                enrolled = int(row['Enrolled'])*2.5
                random_list = get_login_codes(enrolled)

            # Indclude login codes in ExternalDataReference columns
            for code in random_list:
                OSE_info['ExternalDataReference'] = code
                output_panel = output_panel.append(OSE_info, True)

            # Login code path
            login_codes_path = output_login_path + "\\" + school_short + "_logincodes"

            # Concatenate roster info with OSE info if FFT
            if is_FFT:
                final_output = pd.concat([output_panel,roster_part], axis=1)
                login_codes = final_output[['ExternalDataReference','StudentID']]
                print_login_codes(row['School_Name'],login_codes,login_codes_path +".xls")
                print "Number of students for " + school_short + ": " + str(len(roster_part))
            else:
                final_output = output_panel
                login_codes = final_output['ExternalDataReference']
                login_codes.to_csv(login_codes_path +".csv", index=False,header=True)
                print "Number of IDs for " + school_short + ": " + str(len(final_output)) + "\n"

            final_output=final_output.dropna(axis=1,how='all')
            final_output.to_csv(output_panel_path + "\\" + output_name, index=False)

        panel_id = ""
        survey_id = ""

        # Upload panel
        if upload_p or upload==1 or upload==3 :
            r = upload_panel(output_panel_path + "\\" + output_name)
            if r.status_code == 200:
                # Success!
                panel_id = ast.literal_eval(r.text)['Result']['PanelID']
                print "\nSuccessfullly uploaded " + output_name + " with panel ID:\n" + str(panel_id)
            else:
                print "Error uploading panel"

        # Upload survey
        if upload_s or upload==2 or upload==3:
            r = upload_survey(survey_name,survey_template)
            if r.status_code == 200:
                print "SUCCESS"
                survey_id = ast.literal_eval(r.text)['Result']['SurveyID']
                print "\nSuccessfullly uploaded with survey ID:\n" + str(survey_id)
            else:
                print "Error uploading survey"

        if survey_id and panel_id:
            update_response_rates(row,panel_id,survey_id,level)


def usage():
    '''
    Print usage message and exit
    :return:
    '''
    print('Options')
    print('   -r Automatically remove classes with fewer than 5 students (default no)')
    print('   -up Upload panel to qualtrics (default no)')
    print('   -us Upload survey to qualtrics (default no)')
    print('   -c Include custom formatting coded in custom_format.py (default no)')
    print('   -s Include sampling coded in sample.py (default no)')

def admin_survey(profiled_df,direct_upload):
    '''
    Administer survey for schools provided in DataFrame
    '''
    # Default options
    remove = False
    upload_p = False
    upload_s = False
    custom = False
    sampling = False

    # Provide options
    if direct_upload == 0:
        options = raw_input("Provide options, [N] for none, or [Enter] for usage:")
        options = options.split(" ")
        if options[0] and len(options) >= 1:
            if "-r" in options:
                remove = True
            if "-up" in options:
                upload_p = True
            if "-us" in options:
                upload_s = True
            if "-c" in options:
                custom = True
            if "-s" in options:
                sampling = True
            create_panel_from(profiled_df, remove, upload_p, upload_s, custom, sampling,direct_upload)
        else:
            usage()
            admin_survey(profiled_df,direct_upload)
    else:
        create_panel_from(profiled_df,remove,upload_p,upload_s,custom,sampling,direct_upload)

def main(args):
    '''
    Parses command-line arguments and creates panel from first argument

    args: (iterable )profiled school file and, if included, argument to indicate that classes with fewer than 5 should not be removed
    '''
    remove = False
    upload_p = False
    upload_s = False
    custom = False
    sampling = False

    if len(args) >= 1: 
        if "-r" in args:
            remove = True
        if "-up" in args:
            upload_p = True
        if "-us" in args:
            upload_s = True
        if "-c" in args:
            custom = True
        if "-s" in args:
            sampling = True

        print("\nReading from file " + args[0] + "\n")
        try:
            profile_info = pd.DataFrame.from_csv(file_obj, index_col=False)
        except:
            print("Profiled file not found")
            sys.exit()
        create_panel_from(profile_info, remove, upload_p, upload_s, custom, sampling)
    else:
        print('create_panel.py [options] [profiled file.csv]')
        usage()

# Pass all params after program name to our main
if __name__ == "__main__":
    main(sys.argv[1:])			