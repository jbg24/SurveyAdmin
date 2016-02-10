import os
import json

from argparse import ArgumentParser, ArgumentTypeError

'''
Using information from the profiled schools file, create a panel
'''

parser = ArgumentParser()
parser.add_argument('-o', '--outDir', metavar='outDir',
                    help='Where the new json survey will be saved (default: ./)', required=False)

parser.add_argument('-t', '--template',
                    help='Template for qualtrics survey', required=True)

parser.add_argument('-p', '--inPanel',
                    help='Panel to be used for survey', required=True)

parser.add_argument('-n', '--name',
                    help='Name of survey', required=True)

parser.add_argument('-i', '--panelID',
                    help='Panel ID', required=True)

def customize_survey(survey_path,survey_name,panel,out_path,panel_id):
    '''
    Using qualtratics template, customize based on panel information
    :param survey_name:
    :param survey_path:
    :param out_path:
    :return:
    '''

    jsonFile = open(survey_path,"r")
    survey_data = json.load(jsonFile)
    jsonFile.close()

    with open(panel, 'r') as f:
        first_line_panel = f.readline().split(',')
    f.close()

    dict_template = {'VariableType': 'Nominal', 'Type':'Recipient'}

    panel_elements = []
    for element in first_line_panel:
        dict_copy = dict_template.copy()
        dict_copy['Field'] = element
        dict_copy['Description'] = element

        panel_elements.append(dict_copy)

    survey_data['SurveyElements'][1]['Payload']['Flow'][1]['Flow'][0]['EmbeddedData'] = panel_elements
    survey_data['SurveyElements'][1]['Payload']['Flow'][1]['PanelData']['PanelID'] = panel_id

    out_path = os.path.join(out_path,survey_name +'.json')
    outfile = open(out_path, 'w+')
    outfile.write(json.dumps(survey_data))
    outfile.close()

    return out_path

if __name__ == "__main__":

    args = parser.parse_args()

    if not os.path.isfile(args.template):
        raise IOError('The template file {} does not exist.'.format(args.template))

    if not os.path.isfile(args.inPanel):
        raise IOError('The panel file {} does not exist.'.format(args.template))

    # Save in RosterFiles directory if no output directory specified
    if not args.outDir:
        args.outDir = os.getcwd()

    customize_survey(args.template,args.name,args.inPanel,args.outDir,args.panelID)