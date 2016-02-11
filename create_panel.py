### Created to generate panels from Profiled Salesforce file and, if necessary, roster files
### Roster headers should be the following: "Student ID"	"Student's Grade Level"	"Teacher First Name"
###	"Teacher Last Name"	"Teacher ID"	Class Name - Section Number	"Class Period" "Department"	"School Name"	(Teacher's Email is optional)
## TO DO - make sure no ascii characters in panel file 

import sys
import pandas as pd
import random
import datetime
import re
import string
import os
import xlrd
from xlutils.filter import process,XLRDReader,XLWTWriter

from argparse import ArgumentParser, ArgumentTypeError

from qualtrics_upload import upload_panel,upload_survey,activate_survey
from create_survey import customize_survey

'''
Using information from the profiled schools file, create a panel
'''

parser = ArgumentParser()
parser.add_argument('-o', '--outDir', metavar='outDir',
                    help='Parent directory for client folders where panel files, roster info and login'
                         'codes will be saved (default: ./)', required=False)

parser.add_argument('-i', '--inFile', metavar='inFile',
                    help='Profiled schools File to be read in', required=True)

parser.add_argument('-up', '--upload',
                    help='Indicates you want to upload panel and survey, need to include path where response rates'
                         'will be recorded', required=False)

parser.add_argument('-rows', '--rows', metavar='rows',
                    help='Which rows (schools) to make panels for, e.g. 2-5, 7, or A', required=True)


def parseRows(rows):
    '''
    Parse the --rows argument to determine which schools to make panels for
    :param rows: (string) in form 2-5, or 7, or A
    :return: list of rows
    '''

    selection = rows.strip().split(",")

    # Determine which opportunities were selected
    chosen_opps = []

    for nums in selection:
        try:
            if "-" in nums:
                end_values = nums.split("-")
                new_values = range(int(end_values[0]),int(end_values[1])+1)
                chosen_opps.extend(new_values)
            else:
                chosen_opps.append(int(nums))
        except:
             raise ArgumentTypeError("'" + nums + "' is not a range of number. Expected forms like '0-5' or '2'.")

    return chosen_opps


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

def get_ose_info(row,headers):
    '''
    Get OSE info for the panel and return updated panel DataFrame
    :param panel_df: (DataFrame) panel up to this point
    :param profiled_info: (Series) with profiled information
    :return:
    '''

    panel_dict = {}

    # Make school short
    school_short = make_school_short(row['Short'],row['Survey Start Date'],row['Survey Window'])
    print "Processing %s" %school_short
    panel_dict['School_Short'] = [school_short]

    #put 1's for grade that is included in school
    grade_list = str(row['GradeLevels']).split(';')
    for grade in grade_list:
        if grade == '3':
            grade = '3rd'
        else:
            grade = grade + 'th'
        panel_dict[grade] = [1]

    # Set MERig
    if row['FFT'] == True:
        panel_dict['MERig'] = [0]
    else:
        panel_dict['MERig'] = [1]

    panel_dict['School_Name'] = [row['School_Name']]

    for header in headers:
        if row[header]== False:
            panel_dict[header] = [0]
        else:
            panel_dict[header] = [1]

    return panel_dict

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

    return list(random_list)


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

def print_ose_login_codes(data_points,codes_path):
    '''
    Print the login codes for OSE - right now, only the ExternalDataReference field in the panel --> need to make a PDF
    Print two files - one with
    :param school_name:
    :param data_points:
    :param codes_path:
    :return:
    '''
    length_df = len(data_points)
    main_file_length = int(length_df*0.6)
    data_points[:main_file_length].to_csv(codes_path,index=False,header=True)

    main_file_path = os.path.split(codes_path)[0]
    backup_file_name = os.path.split(codes_path)[1].split('.csv')[0] + '_backup.csv'
    backup_path = os.path.join(main_file_path,backup_file_name)
    data_points[main_file_length:].to_csv(backup_path,index=False,header=True)

def print_fft_login_codes(school_name, data_points,codes_path):
    '''
    Using login codes template, print login codes
    :param data_points:
    :param codes_path:
    :return:
    '''

    wbk = xlrd.open_workbook("TemplatesMapsImages/LoginCodeTemplate.xls", formatting_info=True)
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


    sheet_cover.insert_bitmap('TemplatesMapsImages/YTimage.bmp',0,2)
    output_path = os.path.join(codes_path,school_name + '_logincodes.xls')
    wbk_copy.save(output_path)

def output_files(output_df,output_name,school_name,output_path,fft=False):
    '''
    Output panel and login codes
    :param output_df:
    :param output_name:
    :param login_codes:
    :param output_path:
    :return:
    '''

    # Remove schoolname column which was part of roster file
    dfcolumns = output_df.columns.tolist()
    if 'schoolname' in dfcolumns and 'School_Name' in dfcolumns:
        dfcolumns.remove('schoolname')

    # Move login codes to front - required by Qualtrics; others are preference
    dfcolumns.insert(0, dfcolumns.pop(dfcolumns.index('ExternalDataReference')))
    dfcolumns.insert(1, dfcolumns.pop(dfcolumns.index('School_Name')))
    dfcolumns.insert(2, dfcolumns.pop(dfcolumns.index('School_Short')))
    dfcolumns.insert(3, dfcolumns.pop(dfcolumns.index('OE')))
    dfcolumns.insert(4, dfcolumns.pop(dfcolumns.index('FFT')))

    # Create paths
    login_codes_path = os.path.join(output_path,'LoginCodes')
    panels_path = os.path.join(output_path,'Panels')

    if not os.path.exists(login_codes_path):
        os.makedirs(login_codes_path)

    if not os.path.exists(panels_path):
        os.makedirs(panels_path)

    # Print panel
    panel_path = os.path.join(panels_path,output_name)
    output_df.to_csv(panel_path,cols=dfcolumns,index=False)

    # Print login codes
    if fft:
        print_fft_login_codes(school_name,output_df[['ExternalDataReference','StudentID']],login_codes_path)
    else:
        login_codes_path = os.path.join(login_codes_path,school_name + "_logincodes.csv")
        print_ose_login_codes(output_df['ExternalDataReference'],login_codes_path)

    return panel_path

def get_output_name(school_level,school_short):
    '''
    Generate output name for panel
    :return: (String) output name
    '''

    # Format date for file name
    date_today = str(datetime.date.today())
    date_today = re.sub('-','',date_today)

    # Determine school level and output name
    level = school_level.strip().split(' ')
    level = level[0][0] + "S"

    output_name = level + ' PINs_' + date_today + '_' + school_short + '.csv'

    return output_name

def get_survey_template(level,is_minn):
    '''
    Get name of survey template to use
    :param level:
    :return:
    '''

    survey_template = level + "Mastersurvey"
    if is_minn:
        if level == "HS" or level == "MS":
            survey_template = "SSMastersurvey_MN.json"
        else:
            survey_template = "ESMastersurvey_MN.json"
    else:
        survey_template = survey_template + ".json"

    return survey_template

def create_survey_name(profiled_info,level,is_minn):
    '''
    Make name for survey
    :param profiled_info:
    :param level:
    :return:
    '''

    opp_name = str(profiled_info['Opportunity'])
    is_OSE = profiled_info['OE']
    is_FFT = profiled_info['FFT']

    school_name = str(profiled_info['Short']).strip()
    survey_type_text = ""
    if is_OSE:
        survey_type_text = "OSE"
    if is_FFT and survey_type_text == "OSE":
        survey_type_text = "OSE-FFT"
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

    return survey_name

def create_surveys(profiled_info,panel_path,panel_id):
    '''
    Using the information from the profiled file and the panel path, create the customized survey
    :param profiled_info(Series)
    :param panel_path: (string) path to panel
    :return:
    '''

    # Determine school level
    level = str(profiled_info['School Level']).strip().split(' ')
    level = level[0][0] + "S"

    is_minn = False
    if profiled_info['State']=='MN':
        is_minn = True

    survey_name = create_survey_name(profiled_info,level,is_minn)
    survey_template = get_survey_template(level,is_minn)
    out_path = os.path.split(panel_path)[0]

    survey_template_path = os.path.join('QualtricsSurveyTemplates',survey_template)

    return customize_survey(survey_template_path,survey_name,panel_path,out_path,panel_id)

def update_response_rates(profiled_info,panel_id,survey_id,level,rr_path):
    '''
    Get active response rates list and append new info
    :param profiled_info:
    :param panel_id:
    :param survey_id:
    :return:
    '''

    level_dict = {'High School':'year','Middle School':'m_grade','Elementary School':'e_grade'}
    # Create path for output
    new_info = {}
    new_info['SurveyName'] = profiled_info['School_Name']

    if profiled_info['OE'] == True:
        new_info['OSE'] = 1
        new_info['Subgroup'] = level_dict[level]
    else:
        new_info['OSE'] = 0

    if profiled_info['FFT'] == True:
        new_info['FFT'] = 1
        new_info['Subgroup'] = 'linked_grade'
    else:
        new_info['FFT'] = 0

    new_info['SurveyID'] = survey_id
    new_info['PanelID'] = panel_id
    new_info['Enrollment'] = profiled_info['Enrolled']

    if os.path.exists(rr_path):
        current_response_list = pd.DataFrame.from_csv(rr_path,index_col=None)
        current_response_list = current_response_list.append(new_info,ignore_index=True)
        try:
            current_response_list.to_csv(rr_path,index=False)
        except IOError:
            print >> sys.stderr, "Trouble writing to {}".format(rr_path)
    else:
        output_response = pd.DataFrame(new_info,index=[0])
        output_response.to_csv(rr_path,index=False)

def create_panel(profile_info,out,upload):
    '''
    Creates panel from profiled salesforce report

    file_obj: Pandas data frame with profiled school info
    del_less_five: (bool) indicates whether to automatically remove classes with fewer than 5 students
    '''

    # Read in panel headers
    with open('TemplatesMapsImages/PINs_Template_Master.csv') as file_object:
        headers = file_object.read().splitlines()

    out_names = []
    # Loop through each profiled school
    for index, row in profile_info.iterrows():

        out_path = os.path.join(out,row['Opportunity'])

        # Check if missing any profiled school info
        hasNulls = pd.isnull(row).tolist()
        if True in hasNulls:
            print "\n--Missing Profile Info: Skipping row %i in profiled schools file\n" %(index)
            continue

        # Get OSE info
        panel_dict = get_ose_info(row,headers)

        # Number of login codes
        num_rows = 0

        # Read in roster data if necessary and determine length of panel
        if row['FFT']:
            roster_path = row['Roster']

            if not os.path.exists(roster_path):
                print >> sys.stderr, 'The roster file {} does not exist. Skipping row {}'.format(roster_path,index)
                continue

            try:
                roster_file = pd.read_csv(roster_path,index_col=False)
            except IOError:
                raise IOError("The roster file {} could not be opened".format(roster_path))

            num_rows = len(roster_file)
        else:
            num_rows = int(int(row['Enrolled'])*2.5)

        # Extend the dict by the appropriate number of row
        for key,value in panel_dict.iteritems():
            panel_dict[key] = value * num_rows

        # Get login codes
        login_codes =  get_login_codes(num_rows)
        panel_dict['ExternalDataReference'] = login_codes

        # Create DataFrame
        panel_out = pd.DataFrame(panel_dict)
        if row['FFT']:
            panel_out = pd.concat([panel_out,roster_file], axis=1)

        output_name = get_output_name(row['School Level'],panel_dict['School_Short'][0])
        panel_path = output_files(panel_out,output_name,row['School_Name'],out_path,row['FFT'])

        if upload:
            try:

                panel_id = upload_panel(panel_path)
                survey_path = create_surveys(row,panel_path,panel_id)
                survey_name = os.path.split(survey_path)[1].split('.json')[0]
                survey_id = upload_survey(survey_path,survey_name)
                activate_survey(survey_id)
                update_response_rates(row,panel_id,survey_id,row['School Level'],upload)
                out_names.append(survey_name + ',' + 'http://cep.co1.qualtrics.com/SE/?SID='+survey_id)

            except Exception as e:
                print >> sys.stderr, e.response.content
                continue

    return out_names

if __name__ == "__main__":

    args = parser.parse_args()

    if not os.path.isfile(args.inFile):
        raise IOError('The profiled schools file {} does not exist.'.format(args.cleanList))

    try:
        profiled = pd.read_csv(args.inFile)
    except:
        raise IOError("The profiled schools file {} could not be opened".format(args.inFile))

    if args.rows != 'A':
        row_list = parseRows(args.rows)
        if max(row_list) < len(profiled) and min(row_list)>=0:
            profiled = profiled[profiled.index.isin(row_list)]
        else:
            print >> sys.stderr, ("Row values are out of range - must be from 0 to {}".format(str(len(profiled)-1)))

    # Save in RosterFiles directory if no output directory specified
    if not args.outDir:
        args.outDir = os.getcwd()

    survey_urls = create_panel(profiled,args.outDir,args.upload)
    if survey_urls:
        for url in survey_urls:
            print >> sys.stdout, url