"""
   net.py
   COMP9444, CSE, UNSW
"""

from __future__ import print_function
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision

class NetLin(nn.Module):
    # linear network with no activation function
    def __init__(self):
        super(NetLin, self).__init__()
        # INSERT CODE HERE

    def forward(self, x):
        return 0   # CHANGE CODE HERE

    def viz(self): # create and save images
        weights = self.in_out.weight.data
        # INSERT CODE HERE

class NetSkip(nn.Module):
    # network combining direct input-to-output weights
    # with a fully connected hidden layer of 8 nodes
    def __init__(self):
        super(NetSkip, self).__init__()
        # INSERT CODE HERE

    def forward(self, x):
        return 0   # CHANGE CODE HERE

    def viz(self): # create and save images
        weights = self.in_hid.weight.data
        # INSERT CODE HERE

class NetConv(nn.Module):
    # two fully convolutional layers using relu,
    # one fully connected (hidden) layer using relu,
    # and one fully connected (output) layer
    def __init__(self):
        super(NetConv, self).__init__()
        # INSERT CODE HERE

    def forward(self, x):
        return 0   # CHANGE CODE HERE

    def viz(self): # create and save images
        weights = self.conv1.weight.data
        # INSERT CODE HERE

def min_max_scale(w):
    # scale tensor values linearly to the range [0,1]
    w_min = w.min()
    w_max = w.max()
    eps = 0.00000001
    return((w - w_min)/(w_max - w_min + eps))
