import glob
import json
import logging

import numpy as np
import cv2

from submodules.openvino_model import *
from submodules.common_face_utils import *

class numpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(numpyEncoder, self).default(obj)

logging.basicConfig(level=[logging.INFO, logging.DEBUG, logging.WARN, logging.ERROR][0])

with open('thermometer_cfg.json', 'rt') as f:    # read configurations from the configuration file
    config = json.load(f)

# Load OpenVINO Deep-learning models
inference_device = config["system"]["inference_device"]
FD_net = openvino_model(config["dl_models"]["FD_model"], inference_device)
FR_net = openvino_model(config["dl_models"]["FR_model"], inference_device)
LM_net = openvino_model(config["dl_models"]["LM_model"], inference_device)

pictures = glob.glob(os.path.join(config["system"]["image_dir"], '*.jpg'))
num_faces = 0
for pic in pictures:
    in_img = cv2.imread(pic)
    FD_res = FD_net.image_sync_infer(in_img)[FD_net.outblob_names[0]]
    ROIs = get_ROIs(FD_res[0][0])
    if len(ROIs)<1:
        continue
    ROI = find_largest_ROI(ROIs)
    ROI[2:2+4+1] = rescale_ROI(ROI[2:2+4+1], scale_factor=1.2)
    cropped_face = crop_ROI(ROI, in_img)

    LM_res = LM_net.image_sync_infer(cropped_face)[LM_net.outblob_names[0]]
    aligned_face = align_face(cropped_face, LM_res.reshape((5,2)))

    FR_res = FR_net.image_sync_infer(aligned_face)[FR_net.outblob_names[0]]
    feat_vec = FR_res.ravel()

    path, filename = os.path.split(pic)
    base_name, ext = os.path.splitext(filename)
    person_id, person_name = base_name.split('-')[:1+1]

    json_file_name = os.path.join(config["system"]["database_dir"], os.path.splitext(os.path.split(pic)[-1])[0]+'.json')
    record = [person_id, person_name, feat_vec]
    with open(json_file_name, 'wt') as f:
        json.dump(record, f, cls=numpyEncoder)
    logging.info('Registered - {} {}'.format(person_id, person_name))
    num_faces += 1

logging.info('Total {} faces are registered.'.format(num_faces))
