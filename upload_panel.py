__author__ = 'jeremyg'
##
## Script to upload the contents of a csv Qualtrics "panel" or survey file to qualtrics library
##

import sys
import os
import ntpath # To get file from given path in path_leaf()
import requests # To access qualtrics api
import ast

#default global values
root_url = 'https://survey.qualtrics.com/WRAPI/ControlPanel/api.php'
format = "JSON"
token = "M3QW9XL6HnKqmi83rDp6FzeeBOFKKKXRV7kkQe9w"
version = "2.3"
user = "qualtrics@effectivephilanthropy.org"
libid = 'UR_2o5kSVAJAA7Mkqo'

#from stack overflow: http://stackoverflow.com/questions/8384737/python-extract-file-name-from-path-no-matter-what-the-os-path-format
def path_leaf(path):
    '''
    Return only the file name, given a path
    :param path: (string) file path
    :return: only file name
    '''
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)

def upload_panel(panel):
    '''
    Upload csv panel file to qualtrics library

    :param panel: (string) path to panel csv file
    :return: request response
    '''
    #default local values
    panel_name = path_leaf(panel)
    exref= 1
    request = "importPanel"
    email = 0
    headers = 1
    alled = 1

    # Parameters
    params = {'Name': panel_name, 'Format': format, 'ExternalRef': exref,'Request': request, \
              'Email': email, 'Token': token, 'Version': version, 'User': user, \
              'LibraryID': libid, 'ColumnHeaders': headers, 'AllED': alled}

    # Post request to Qualtrics
    with open(panel, 'rb') as up_panel:
        return requests.post(root_url, params=params, data=up_panel)

def upload_survey(survey_name, survey_template):
    '''
    Upload template survey and return Qualtrics request response

    survey_name: (string) to be displayed in qualtrics
    survey_template: (string) path of specific template
    return: requests response
    '''
    request = "importSurvey"
    import_type = "QSF"

    #Parameters
    params = {'Name': survey_name, 'Format': format,'Request': request, \
                'Token': token, 'ImportFormat': import_type, 'Version': version, 'User': user, \
              }

    # Post request to Qualtrics
    with open(survey_template, 'rb') as up_survey:
        return requests.post(root_url, params=params, data=up_survey)

def upload_all():
    '''
    Select client folders with exisitng panels and upload panels and create surveysd
    '''
    client_path = os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..\\ClientFolders'))
    current_clients = os.listdir(client_path)
    client_count = range(0,len(current_clients))

    print "\n"
    for num, client in zip(client_count,current_clients):
        print num + "  " + client

    selection = raw_input("\nSelect the schools you wish to upload panels and surveys for (e.g. 5,10-16,20 or A for all:)")
    selection = selection.strip().split(",")

    chosen_clients = []
    # Check if all schools were chosen
    if len(selection) == 1 and 'A' in selection:
        chosen_clients = client_count[:]
    else:
        for nums in selection:
            if "-" in nums:
                end_values = nums.split("-")
                new_values = range(int(end_values[0]),int(end_values[1])+1)
                chosen_clients.extend(new_values)
            else:
                chosen_clients.append(int(nums))



#testing
if __name__ == "__main__":
    r = upload_survey()

    if r.status_code == 200:
        print "SUCCESS"
        survey_id = ast.literal_eval(r.text)['Result']['SurveyID']
        print "\nSuccessfullly uploaded with survey ID:\n" + str(survey_id)
    else:
        print "Error uploading panel"
    '''
    if len(sys.argv[1:]) == 1:
        if os.path.isfile(sys.argv[1]):
            filepath = sys.argv[1]
            with open(filepath, 'rb') as panelfile:
                for line in panelfile:
                    print line
            checking = raw_input("Import each panel above to Qualtrics (y/n)?")
            if checking == 'y':
                with open(filepath, 'rb') as panelfile:
                    for line in panelfile:
                        r = upload_panel(line.strip())
                        if r.status_code == 200:
                            # Success!
                            panel_id = ast.literal_eval(r.text)['Result']['PanelID']
                            print "successfullly uploaded " + path_leaf(line) + "with panel ID:" + str(panel_id) + "\n"
                        else:
                            print "Error uploading panel"
            else:
                print "Quitting"
                sys.exit()
    else:
        print "Usage: upload_panel.py panellist.csv"
    '''