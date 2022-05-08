import asyncio
import io
import glob
import os
import sys
import time
import uuid
import requests
from urllib.parse import urlparse
from io import BytesIO
# To install this module, run:
# python -m pip install Pillow
from PIL import Image, ImageDraw
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.face.models import TrainingStatusType, Person, QualityForRecognition

key = os.environ['frd_key']
endpoint = os.environ['frd_endpoint']

# print(endpoint)

# Authenticate the client
# Create an authenticated FaceClient.
face_client = FaceClient(endpoint, CognitiveServicesCredentials(key))



# Detect and analyze faces
# Detect a face in an image that contains a single face
single_face_image_url = 'https://www.biography.com/.image/t_share/MTQ1MzAyNzYzOTgxNTE0NTEz/john-f-kennedy---mini-biography.jpg'

single_image_name = os.path.basename(single_face_image_url)


# Use detection model 3 to get better performance
# The below function on the right returns a list of faces from the image supplied
# We use a particular detection model according to use case
detected_faces = face_client.face.detect_with_url(url=single_face_image_url, detection_model='detection_03')

if not detected_faces:
    raise Exception('No face detected from image {}'.format(single_image_name))

  

# Display the detected face id in the first single face image
# Face ids are used for comparison to faces(their ids)

# for face in detected_faces: print(face)

# we eill save the below id for use in find similar faces service
first_image_face_id=detected_faces[0].face_id

print("This is the id of the face detected {}".format(first_image_face_id))


# We need to draw a rectangle around the detected face
# Look into the face_rectangle object 
def getRectangle(faceDictionary):
  rect = faceDictionary.face_rectangle
  print("this is the rect object {}".format(rect))
  
  left = rect.left
  top = rect.top
  right = left+rect.width
  bottom = top + rect.width

  

  return ((left,top),(right,bottom))


def drawFaceRectangles():
  # Download the image from the url
  response = requests.get(single_face_image_url)

  # print("this is the resopnse object {}".format(response.content))
  # The response content that we are receiving is a file full of bytes that we open as an image 
  img = Image.open(BytesIO(response.content))

  # print("this is what is there in the img variable {}".format(img))
  
  # For each face returned use the face rectangle and draw a red box
  # print('Drawing rectangle around face... see popup for results.')
  draw = ImageDraw.Draw(img);
  for face in detected_faces:
    draw.rectangle(getRectangle(face), outline="red")

  # Display the image in the default image browser
  img.show()

  
# drawFaceRectangles()

# Our next objective is to take the image of a person or (multiple people and look to find the identity of each face in the image(facial recognition search). It compares each detected face to a PersonGroup, a database of person objects whose features are known. 

# We need to train it over a set of images to make the database searchable

# Create a PersonGroup

# Create a person group id 
# PERSON_GROUP_ID=str(uuid.uuid4()) # Assign a random number or name it anything
PGID=str(uuid.uuid4())

TPGID=str(uuid.uuid4())

# Create the person group
# print("person group:",PGID)

face_client.person_group.create(person_group_id=PGID,name=PGID)

# Define woman friend
woman = face_client.person_group_person.create(PGID,"woman")

# Define man friend
man = face_client.person_group_person.create(PGID,"man")

# Define child friend
child = face_client.person_group_person.create(PGID,"child")

# Above we have created a person group and three sets of people in that person group

# Next we need to assign faces to persons

# Detect faces and register to correct Person

# Find all the jpeg images of friends in the working directory
woman_images = [file for file in glob.glob('*jpg') if file.startswith('w')]
man_images = [file for file in glob.glob('*jpg') if file.startswith('m')]
child_images = [file for file in glob.glob('*jpg') if file.startswith('ch')]

# print(woman_images)

# Add to a woman Person
for image in woman_images:
  w = open(image,'r+b')
  # Check if the image is of sufficient quality for recognition
  sufficientQuality = True
  detected_faces = face_client.face.detect_with_url(url=single_face_image_url,detection_model="detection_03",recognition_model="recognition_04",return_face_attributes=['qualityForRecognition'])
  for face in detected_faces:
    if face.face_attributes.quality_for_recognition != QualityForRecognition.high:
      sufficientQuality=False
      break
    if not sufficientQuality : continue
    face_client.person_group_person.add_face_from_stream(PGID,woman.person_id,w)  

for image in man_images:
  m = open(image,'r+b')
  # Check if the image is of sufficient quality for recognition
  sufficientQuality = True
  detected_faces = face_client.face.detect_with_url(url=single_face_image_url,detection_model="detection_03",recognition_model="recognition_04",return_face_attributes=['qualityForRecognition'])
  for face in detected_faces:
    if face.face_attributes.quality_for_recognition != QualityForRecognition.high:
      sufficientQuality=False
      break
    if not sufficientQuality : continue
    face_client.person_group_person.add_face_from_stream(PGID,man.person_id,m)  


for image in child_images:
  c = open(image,'r+b')
  # Check if the image is of sufficient quality for recognition
  sufficientQuality = True
  detected_faces = face_client.face.detect_with_url(url=single_face_image_url,detection_model="detection_03",recognition_model="recognition_04",return_face_attributes=['qualityForRecognition'])
  for face in detected_faces:
    if face.face_attributes.quality_for_recognition != QualityForRecognition.high:
      sufficientQuality=False
      break
    if not sufficientQuality : continue

time.sleep(60)


face_client.person_group_person.add_face_from_stream(PGID,child.person_id,c)  


# We can also create PersonGroup from remote images referenced by a URL. It will use the add_face_from_url method

# Train the person group
# Once we have assigned faces, we must train the PersonGroup so that it can identify the visual features associated with each of its person objects. The following code calls the asyncronous train method and polls the result, priting the status to the console

# Train the person group

print()
print('Training the person group...')

face_client.person_group.train(PGID)

# As the above operation is an asynchronous operation we can query about its status and do something accordingly


while(True):
  training_status = face_client.person_group.get_training_status(PGID)
  print("Training status: {}".format(training_status.status))
  print()
  if(training_status.status is TrainingStatusType.succeeded):
    break
  elif (training_status.status is TrainingStatusType.failed):
    face_client.person_group.delete(person_group_id=PGID)
    sys.exit("Training the person group has failed.")
  time.sleep(5)














# Delete the main person group.
face_client.person_group.delete(person_group_id=PGID)
print("Deleted the person group {} from the source location.".format(PGID))
print()
  

