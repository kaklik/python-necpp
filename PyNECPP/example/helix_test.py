import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt
import matplotlib as mpl

from PyNEC import *
from antenna_util import *

from context_clean import *

import math

brass_conductivity = 15600000 # mhos
copper_conductivity = 1.45e7 # Copper
ground_conductivity = 0.002
ground_dielectric = 10

tl_impedance = 75

def n_seg(freq, length):
  wavelength = 3e8/(1e6*freq)
  return (2 * (int(math.ceil(77*length/wavelength))/2)) + 1

def sc_quad_helix(freq, height, diameter, wire_diameter = 0.02):
    
    nec = context_clean(nec_context())
    nec.set_extended_thin_wire_kernel(True)
    
    geo = geometry_clean(nec.get_geometry())

    wire_r = wire_diameter/2;
    helix_r = diameter/2;
    
    
    print "Wire Diameter %s" % (wire_r * 2)
    
    helix_turns = 0.5
    
    # helix loop 
    helix_twist_height = height / helix_turns
    geo.helix(tag_id=1, nr_segments=n_seg(freq,height), spacing=helix_twist_height, lenght=height, start_radius=np.array([helix_r, 0]), end_radius=np.array([helix_r, 0]), wire_radius=wire_r)
    geo.move(rotate_z=90, copies=3, tag_inc=1)
    geo.wire(tag_id=10, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([helix_r, 0, height]), radius=wire_r)
    geo.wire(tag_id=11, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([0, helix_r, height]), radius=wire_r)
    geo.wire(tag_id=12, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([-helix_r, 0, height]), radius=wire_r)
    geo.wire(tag_id=13, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([0, -helix_r, height]), radius=wire_r)
    
    # Everything is copper
    #nec.set_wire_conductivity(copper_conductivity)

    nec.geometry_complete(ground_plane=False)

    return nec

sc_quad_helix(143,0.8,2*1.62100E-01)


