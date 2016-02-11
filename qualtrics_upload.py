'''
Script to upload the contents of a csv Qualtrics "panel" or survey file to qualtrics library
'''

import sys
import os
import ntpath # To get file from given path in path_leaf()
import requests # To access qualtrics api
import ast
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('-iP', '--inPanel',nargs = '+',
                    help='Panel file[s] to be read in and uploaded to Qualtrics', required=False)

parser.add_argument('-iS', '--inSurvey', metavar='inSurvey', nargs=2,
                    help='Survey file and name to be read in and uploaded to Qualtrics', required=False)

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
    params = {'Name': panel_name, 'Format': format, 'ExternalRef': exref,'Request': request,
              'Email': email, 'Token': token, 'Version': version, 'User': user,
              'LibraryID': libid, 'ColumnHeaders': headers, 'AllED': alled}

    # Post request to Qualtrics
    with open(panel, 'rb') as up_panel:
        r = requests.post(root_url, params=params, data=up_panel)
        if not r.raise_for_status():
            panel_id = ast.literal_eval(r.text)['Result']['PanelID']
            print "\nSuccessfullly uploaded " + panel + " with panel ID:\n" + str(panel_id)

    return panel_id

def activate_survey(survey_id):
    '''
    Activate survey with survey_id
    :param survey_id:
    :return:
    '''
    request = "activateSurvey"

    #Parameters
    params = {'Format': format,'Request': request,
                'Token': token, 'Version': version, 'User': user, 'SurveyID':survey_id
              }

    r = requests.post(root_url, params=params)
    if not r.raise_for_status():
        print "\nSuccessfullly activated survey id " + survey_id

def upload_survey(survey_template, survey_name):
    '''
    Upload template survey and return Qualtrics request response

    survey_name: (string) to be displayed in qualtrics
    survey_template: (string) path of specific template
    return: requests response
    '''
    request = "importSurvey"
    import_type = "QSF"

    #Parameters
    params = {'Name': survey_name, 'Format': format,'Request': request,
                'Token': token, 'ImportFormat': import_type, 'Version': version, 'User': user,
              }

    # Post request to Qualtrics
    with open(survey_template, 'rb') as up_survey:
        r = requests.post(root_url, params=params, data=up_survey)
        if not r.raise_for_status():
            survey_id = ast.literal_eval(r.text)['Result']['SurveyID']
            print "\nSuccessfullly uploaded " + survey_name + " with survey ID:\n" + str(survey_id)

    return survey_id

#testing
if __name__ == "__main__":

    args = parser.parse_args()

    #if not args.inPanel and not args.inSurvey:
    #    parser.print_help()

    if args.inPanel:
        for panel in args.inPanel:
            if not os.path.exists(panel):
                print >> sys.stderr, ('The panel file {} does not exist.'.format(panel))
            try:
                upload_panel(panel)
            except requests.exceptions.RequestException as e:
                print e.response.content

    if args.inSurvey:
        if not os.path.isfile(args.inSurvey[0]):
            raise IOError('The survey file {} does not exist.'.format(args.inSurvey[0]))
        try:
            upload_survey(args.inSurvey[0], args.inSurvey[1])
        except requests.exceptions.RequestException as e:
            print e.response.content


