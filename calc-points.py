#!/usr/bin/env python
"""
You can use this script to calculate the points for the level up form 
submissions. You can see the files you need to supply and their 
format with --help.
"""

import csv
import pprint
from datetime import datetime
import argparse
import os.path
import collections
from collections import OrderedDict


def test_file(fn):
    if not os.path.isfile(fn):
        print("{0} does not exist.".format(fn))
        exit()
    return fn


pp = pprint.PrettyPrinter(indent=4)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("-p", "--points", required=True, dest="point_submissions_fn",
	help="point submissions file, expects columns: Timestamp, Public Name, Name, Email, Code (in any order)")
ap.add_argument("-r", "--reference", required=True, dest="reference_fn",
	help="points reference file, expects columns: Code, Points (in any order)")
ap.add_argument("-o", "--output", required=True, dest="output_fn",
	help="csv file output of points per person")
args = vars(ap.parse_args())


print("testing input params")
point_submissions_fn = test_file(args["point_submissions_fn"])
reference_fn = test_file(args["reference_fn"])
output_fn = args["output_fn"]

codes = {}
submissions = {}
people = {}

submissions_col_headers = ["Timestamp", "Public Name", "Name", "Email", "Code"]
reference_col_headers = ["Code", "Points"]
output_col_headers = ["Public Name", "Name", "Email", "Points"]

# collect all point values in one dict
with open(reference_fn) as csvfile:
    csv_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    file_headers = csv_reader.fieldnames
    for header in reference_col_headers:
        if header not in file_headers:
            print(header + " column not in " + reference_fn)
            exit()

    for row in csv_reader:
        if row["Code"] != "":
            codes[row["Code"]] = int(row['Points'])

# collect all submissions in one dict
with open(point_submissions_fn) as csvfile:
    csv_reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    file_headers = csv_reader.fieldnames
    for header in submissions_col_headers:
        if header not in file_headers:
            print(header + " column not in " + point_submissions_fn)
            exit()

    sub_counter = 1
    for row in csv_reader:
        person = None
        submission = {"id": sub_counter,
                    "public_name": row["Public Name"],
                    "name": row["Name"],
                    "email": row["Email"],
                    "code": row["Code"],
                    }
        person = people.get(str([submission["name"]]))
        if person is None:
            submission["points"] = 0
            person = submission
            people[submission["name"]] = person

        points = person["points"]
        person["points"] = points + codes[person["code"]]

#for debugging
#print("Available Codes:")
#pp.pprint(codes)
#print("Points:")
#pp.pprint(people)

def to_output_format(person):
    out_person = OrderedDict()
    out_person["Public Name"] = person["public_name"]
    out_person["Name"] = person["name"]
    out_person["Email"] = person["email"]
    out_person["Points"] = person["points"]
    return out_person

out_people = []
for key, person in people.items():
    out_people.append(to_output_format(person))

with open(output_fn, 'w') as csvfile:
    out_writer = csv.DictWriter(csvfile, fieldnames=output_col_headers, quoting=csv.QUOTE_ALL)
    out_writer.writeheader()
    out_writer.writerows(out_people)