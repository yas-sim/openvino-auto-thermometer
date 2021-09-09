import glob
import json

import numpy as np
import cv2

from config import *
from openvino_model import *
from common_face_utils import *

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

# Load OpenVINO Deep-learning models
config = {'CACHE_DIR' : './cache'}
FD_net = openvino_model(FD_model, 'GPU', config=config)
FR_net = openvino_model(FR_model, 'GPU', config=config)
LM_net = openvino_model(LM_model, 'GPU', config=config)

pictures = glob.glob(os.path.join(image_dir, '*.jpg'))
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

    json_file_name = os.path.join(database_dir, os.path.splitext(os.path.split(pic)[-1])[0]+'.json')
    record = [person_id, person_name, feat_vec]
    with open(json_file_name, 'wt') as f:
        json.dump(record, f, cls=numpyEncoder)
    print('[INFO] Registered -', person_id, person_name)
    num_faces += 1

print('[INFO] Total', num_faces, 'faces are registered.')
