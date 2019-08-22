""" This version is written in Python 3.7"""

import json
import os
import io
import tqdm 

import panoptes_client
from panoptes_client import SubjectSet, Subject, Project, Panoptes
import pandas as pd

with open('../login.json', 'r') as f:
    zooniverse_login = json.load(f)
Panoptes.connect(**zooniverse_login)

#Project id (dummy project 7931) or Galaxy Zoo (galaxy_zoo_id == '5733')
project = Project("7931")

with open('../test.json') as json_file:
    data = json.load(json_file)

while True:
    location = '/Users/skruk/Documents/Work_in_progress/EAGLE_zoo/EAGLE_subset'
    if location == '.':
        location = os.getcwd()
        break
    else:
        if os.path.exists(location):
            break
        else:
            print('That entry is not a valid path for an existing directory')
            retry = input('Enter "y" to try again, any other key to exit' + '\n')
            if retry.lower() != 'y':
                quit()

#  load the list of image files found in the directory:
#  The local file name will be uploaded as metadata with the image
#file_types = ['png', 'png']

i=0 

subject_metadata = {}

for key, entry in data["#img_name"].items():
        print(entry)
        subject_metadata[entry] = {'Filename': entry}
        for k in data.keys():
            subject_metadata[entry][k] = data[k][str(i)]
        subject_metadata[entry]['metadata_message'] = 'Metadata is available in [Talk](+tab+https://www.zooniverse.org/projects/zookeeper/galaxy-zoo/talk)'
        print(entry)
        i=i+1
print('Found ', len(subject_metadata), ' files to upload in this directory.')


# input the subject set name the images are to be uploaded to
set_name = input('Entry a name for the subject set to use or create:' + '\n')
previous_subjects = []

try:
    # check if the subject set already exits
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    print('You have chosen to upload ', len(subject_metadata), ' files to an existing subject set', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    print('\n', 'It may take a while to recover the names of files previously uploaded, to ensure no duplicates')
    for subject in subject_set.subjects:
        previous_subjects.append(subject.metadata['Filename'])

except StopIteration:
    print('You have chosen to upload ', len(subject_metadata), ' files to an new subject set ', set_name)
    retry = input('Enter "n" to cancel this upload, any other key to continue' + '\n')
    if retry.lower() == 'n':
        quit()
    # create a new subject set for the new data and link it to the project above
    subject_set = SubjectSet()
    subject_set.links.project = project
    subject_set.display_name = set_name
    subject_set.save()

print('Uploading subjects, this could take a while!')
new_subjects = 0
for filename, metadata in tqdm.tqdm(subject_metadata.items()):
    try:
        if filename not in previous_subjects:
            subject = Subject()
            subject.links.project = project
            subject.add_location(location + '/' + filename)
            subject.metadata.update(metadata)
            subject.save()
            subject_set.add(subject.id)
            new_subjects += 1

    except panoptes_client.panoptes.PanoptesAPIException:
        print('An error occurred during the upload of ', filename)
print(new_subjects, 'new subjects created and uploaded')
print('Uploading complete, Please wait while the full subject listing is prepared and saved in')
print('"Uploaded subjects.csv" in the drive with the original images')

uploaded = 0
with open(location + os.sep + 'Uploaded subjects.csv', 'wt') as file_up:
    file_up.write('subject.id' + ',' + 'Filename' + '\n')
    subject_set = SubjectSet.where(project_id=project.id, display_name=set_name).next()
    for subject in subject_set.subjects:
        uploaded += 1
        file_up.write(subject.id + ',' + list(subject.metadata.values())[1] + '\n')
    print(uploaded, ' subjects found in the subject set, see the full list in Uploaded subjects.csv.')
