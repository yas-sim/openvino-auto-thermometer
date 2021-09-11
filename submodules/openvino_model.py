import os, sys
import logging

import numpy as np
import cv2

from openvino.inference_engine import IECore

class openvino_model:
    ie = IECore()
    def __init__(self, model_file = None, device='CPU', config='', num_requests=1):
        self.fpath = None
        self.fbase = None
        self.fname = None
        self.net = None
        self.inblob_names = None
        self.outblob_names = None
        self.inputs = None
        self.outputs = None        
        if not model_file is None:
            self.load_model(model_file, device=device, config=config, num_requests=num_requests)

    def load_model(self, model_file, device='CPU', config='', num_requests=1, verbose=True):
        model_info = {}
        if '.' in model_file:
            base, ext = os.path.splitext(model_file)
        else:
            base = model_file
        self.fpath, self.fbase = os.path.split(base)
        self.fname = base
        logging.info('Loading a DL model - {}...'.format(self.fbase))
        self.net = openvino_model.ie.read_network(base+'.xml', base+'.bin')
        self.inblob_names = list(self.net.input_info)
        self.outblob_names = list(self.net.outputs)
        self.inputs  = {inblob  : self.net.input_info[inblob].tensor_desc.dims for inblob  in self.inblob_names  }
        self.outputs = {outblob : self.net.outputs[outblob].shape              for outblob in self.outblob_names }
        self.inf_inputs = { inblob : None for inblob in self.inblob_names }   # template for inference input
        self.exe_net = openvino_model.ie.load_network(self.net, device, config=config, num_requests=num_requests)

    def image_sync_infer(self, img):
        if len(self.inputs)>1:
            print('[ERROR] Only single input model is supported.')
            return None
        inblob = self.inblob_names[0]
        shape = self.inputs[inblob]
        tmpimg = cv2.resize(img, shape[2:])                 # resize
        #tmpimg = cv2.cvtColor(tmpimg, cv2.COLOR_BGR2RGB)
        tmpimg = tmpimg.transpose((2,0,1))                  # packed pixel -> planer
        tmpimg = tmpimg.reshape(shape)                      # reshape
        self.inf_inputs[inblob] = tmpimg
        res = self.exe_net.infer(self.inf_inputs)
        return res
