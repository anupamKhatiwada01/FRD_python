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


# We need to draw a rectangle around the detected face
def getRectangle(faceDictionary):
  rect = faceDictionary.face_rectangle
  left = rect.left
  top = rect.top
  right = left+rect.width
  bottom = top + rect.width

  

  return ((left,top),(right,bottom))


def drawFaceRectangles():
  # Download the image from the url
  response = requests.get(single_face_image_url)
  img = Image.open(BytesIO(response.content))

  # For each face returned use the face rectangle and draw a red box
  print('Drawing rectangle around face... see popup for results.')
  draw = ImageDraw.Draw(img);
  for face in detected_faces:
    draw.rectangle(getRectangle(face), outline="red")

  # Display the image in the default image browser
  img.show()

  
drawFaceRectangles()








