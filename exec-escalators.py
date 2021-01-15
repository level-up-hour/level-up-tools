#!/usr/bin/env python
"""
You can use this script to find escalators and submit entries for 
when an escalator has occurred. An "escalator" is when repeated actions
cause bonus points. For example, if you attend multiple shows, you get 
some bonus points. You can see the files you need to supply and their
format with --help.
"""

import csv
import pprint
from datetime import datetime
import argparse
import os.path
import collections
from collections import OrderedDict
import requests
import configparser

def test_file(fn):
    if not os.path.isfile(fn):
        print("{0} does not exist.".format(fn))
        exit()
    return fn

def mk_int(s):
    if s != None:
        s = s.strip()
        return int(s) if s else 0
    return 0

pp = pprint.PrettyPrinter(indent=4)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("-c", "--config", required=True, dest="config_fn",
	help="config file: see template in calc-points.ini.sample")
ap.add_argument("-p", "--points", required=True, dest="point_submissions_fn",
	help="point submissions file, expects columns: Timestamp, Public Name, Name, Email, Code (in any order)")
ap.add_argument("-r", "--reference", required=True, dest="reference_fn",
	help="points reference file, expects columns: Code, Points (in any order)")
args = vars(ap.parse_args())

print("testing input params")
config_fn = test_file(args["config_fn"])
point_submissions_fn = test_file(args["point_submissions_fn"])
reference_fn = test_file(args["reference_fn"])

config = configparser.ConfigParser()
config.read(config_fn)

submission_info = config['Form Submission']

groups = {}
escalators = {}
submissions = {}
people = {}

submissions_col_headers = ["Timestamp", "Public Name", "Name", "Email", "Code"]
reference_col_headers = ["Code", "Points", "Escalator Group", "Escalator Count Target"]
#output_col_headers = ["Public Name", "Name", "Email", "Points"]
output_col_headers = ["Public Name", "Points"]

# collect all code information in one dict
with open(reference_fn) as csvfile:
    csv_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    file_headers = csv_reader.fieldnames
    for header in reference_col_headers:
        if header not in file_headers:
            print(header + " column not in " + reference_fn)
            exit()

    for row in csv_reader:
        # ignores the "Escalator" column becuase it is legacy, 
        # instead assumes it is an escalator if it has a target
        target = mk_int(row["Escalator Count Target"])
        group =  mk_int(row['Escalator Group'])
        if row["Code"] != "" and target > 0:
            groups[row["Code"]] = { 
                "target": target,
                "group": group
            }
        if row["Code"] != "" and group > 0:
            if row["Code"] not in groups:
                escalators[row["Code"]] = group

# collect all submissions in one dict
with open(point_submissions_fn) as csvfile:
    csv_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    file_headers = csv_reader.fieldnames
    for header in submissions_col_headers:
        if header not in file_headers:
            print(header + " column not in " + point_submissions_fn)
            exit()

    for row in list(csv_reader):
        person = None
        submission = {
            "public_name": row["Public Name"],
            "name": row["Name"],
            "email": row["Email"],
            "code": row["Code"]
            }

        person = people.get(str(submission["email"]))
        if person is None:
            person = {}
            person["submissions"] = {}
            person["group_counts"] = {}

        person["submissions"][submission["code"]] = submission
        if submission["code"] in escalators:
            group = escalators[submission["code"]]
            if group not in person["group_counts"]:
                person["group_counts"][group] = 0
            person["group_counts"][group] += 1

        people[submission["email"]] = person

escalations = {}

for esc_code, esc_info in groups.items():
    group = esc_info['group']
    for person_id in people:
        person = people[person_id]
        if ('group_counts' in person and 
            group in person['group_counts']  and
            person['group_counts'][group] >= esc_info['target']):
            
            #check if the code is already in submissions
            submitted = False
            if esc_code in person["submissions"]:
                submitted = True

            if 'escalations' not in person:
                person['escalations'] = {}

            person['escalations'][esc_code] = submitted

def submit_escalation(public_name, name, email, code):
    #print("using the url template and parse the needful: {} {} {} {}".format(public_name, name, email, code))
    form_data = {
        submission_info['PublicNameFieldname'] : public_name, 
        submission_info['NameFieldname'] : name, 
        submission_info['EmailFieldname'] : email, 
        submission_info['CodeFieldname'] : code
    }
    r = requests.post(submission_info['url'], data=form_data)  
    return (r.status_code == requests.codes.OK)

for person_id, person in people.items():
    if 'escalations' in person:
        for esc_code, submitted in person['escalations'].items():
            if not submitted:
                #grab the theoretical most recent for the indentifying info
                person_info = list(person['submissions'].items())[-1][1]
                if submit_escalation(person_info['public_name'], person_info['name'], person_id, esc_code):
                    print("Submitted {} on behalf of {}".format(esc_code, person_id))
                else:
                    print("Failed to submit {} on behalf of {}".format(esc_code, person_id))
