# Administer YouthTruth Surveys

import os
import pandas as pd
from common import command_line, menu
#from lib.langhelp import para_error
#from lib.syshelp import clrscr
from get_sf_report import get_report,choose_schools
from create_panel import admin_survey
from upload_panel import upload_all

def create_folders():
    '''
    For select opportunities create client folders to contain panels and roster data
    '''

    try:
        current_profiled = pd.read_csv("Profiles/ProfiledSchools.csv")
        print ""
        print current_profiled['Opportunity'].to_string()
        selection = raw_input("Select the opportunities you wish to create folders for (e.g. 5,10-16,20 or A for all):")
        selection = selection.strip().split(",")

        # Determine which opportunities were selected
        chosen_opps = []
        if len(selection) == 1 and 'A' in selection:
            chosen_opps = set(current_profiled['Opportunity'].tolist())
        else:
            for nums in selection:
                if "-" in nums:
                    end_values = nums.split("-")
                    new_values = range(int(end_values[0]),int(end_values[1])+1)
                    chosen_opps.extend(new_values)
                else:
                    chosen_opps.append(int(nums))

            chosen_opps = set(current_profiled[current_profiled.index.isin(chosen_opps)]['Opportunity'].tolist())

        # Create folders for selected opportunities
        output_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..\\ClientFolders'))

        for opp in chosen_opps:
            output_opp = output_path + "\\" + opp
            if not os.path.exists(output_opp):
                os.makedirs(output_opp)
                os.makedirs(output_opp + "\\Panels")
                os.makedirs(output_opp + "\\RosterData")
                os.makedirs(output_opp + "\\LoginCodes")

    except:
        "Profiled Schools Report file does not exist -- run step 1 first to get it from Salesforce"

def start_screen_input():
    #Prompt
    print ''
    print 'Youthtruth Survey Administration Toolkit'
    print 'Please select your options:'
    print ''
    print '     1. Create/Update Salesforce Profiled Schools Report (located in Profiles)'
    print '     2. Create folders for clients in ProfiledSchools file'
    print '     3. Select schools from Profiled Schools Report to create surveys/panels '
    print '     4. Select clients to upload panels and/or create surveys in Qualtrics'
    print ''
    usrinput = menu.get_next_step('Enter your options here: ')
    return usrinput


def execute():
    parsed = command_line.parse_args()
    #settings.override_config(parsed.config)
    #Clear screen
    opt = start_screen_input()

    # Get Salesforce report of profiled schools
    if opt == '1':
        get_report()

    # Create folders for opportunites
    elif opt == '2':
        create_folders()
    # Choose which surveys to administer and include options
    elif opt == '3':

        schools_to_profile = choose_schools()
        print "\nYou have chosen to create panels for: \n"
        print schools_to_profile[['Opportunity','School_Name']]
        cont = raw_input("\nIs this correct? [y/n]")

        if cont == 'y':
            admin_survey(schools_to_profile,0)
        else:
            "\n Returning to main menu"
    elif opt == '4':
        schools_to_profile = choose_schools()
        print "\nYou have chosen to upload panels and/or surveys for: \n"
        print schools_to_profile[['Opportunity','School_Name']]
        cont = raw_input("\nIs this correct? [y/n]")
        if cont == 'y':
            opts = raw_input("\nUpload panel, survey, or both? [pan/surv/both]")
            choices = {'pan': 1, 'surv':2, 'both':3}
            if opts in choices.keys():
                admin_survey(schools_to_profile,choices[opts])
            else:
                 "\n Option not recognized. Returning to main menu"
        else:
            "\n Returning to main menu"
    else:
        print "\nCommand not recognized\n"

    execute()


if __name__ == "__main__":
    execute()
