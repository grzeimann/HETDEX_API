import sys
import numpy as np
import matplotlib.pyplot as plt
import os.path as op
import ipywidgets as widgets
from IPython.display import Image
from ipywidgets import interact, interactive
from hetdex_api.detections import *

# set up classificaiton dictionary                                                                     
class classification_info:
    def __init__(self, detectlist):
        self.detectid = detectlist
        self.vis_class = np.chararray(np.size(detectlist), 15)
        self.comment = np.chararray(np.size(detectlist), 60)
    def add(self, detectid_i, vis_class_i, comment_i):
        ix = np.where(self.detectid == detectid_i)
        self.vis_class[ix] = vis_class_i
        self.comment[ix] = comment_i
        

def main_display(x):
    detectid = detectbox.value
    elix_dir = '/scratch/03261/polonius/jpgs'
    file_jpg = op.join(elix_dir, "egs_%d" %(detectid//100000), str(detectid) + '.jpg')
    display(Image(file_jpg))
    display(classification)
    display(notes)
    display(widgets.HBox([submitbutton, picklebutton]))
    submitbutton.on_click(on_button_click)

def on_button_click(b):
    class_info.add(detectbox.value, classification.value, notes.value)
    detectbox.value +=1


detects = Detections('hdr1')

detectlist = detects.detectid

class_info = classification_info(detectlist)

detectbox = widgets.BoundedIntText(
    value=7,
    min=1000000000,
    max=1000690798,
    step=1,
    description='DetectID:',
    disabled=False
)

classification = widgets.ToggleButtons(
    options=['OII Galaxy', 'LAE Galaxy', 'Star', 'Nearby Galaxy', 'Other Line', 'Artifact','Junk'],
    description='Type:',
    disabled=False,
    button_style='', # 'success', 'info', 'warning', 'danger' or ''
    tooltips=['Low-z OII[3727] emitters', 
              'Distant high-z LAE[1216] emitters',
              'Object is a star, spectrum has no emission',
              'Nearby galaxy, likely Hbeta[4861] or OIII[5007] emitter',
              'Choose this if you are sure its CIV or some other emission',
              'Detector Artifact/cosmic ray',
              'Junky - low SN, very hard to tell']
)
notes = widgets.Text(
    value='',
    placeholder='Enter any comments here',
    description='Comments:',
    disabled=False
)
submitbutton = widgets.Button(description="Submit Classification", button_style='success')
picklebutton = widgets.Button(description="Save Progress", button_style='success')

interact(main_display, x=detectbox)
