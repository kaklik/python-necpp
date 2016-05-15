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

def sc_quad_helix(height, diameter, wire_diameter = 0.02):
    
    nec = context_clean(nec_context())
    nec.set_extended_thin_wire_kernel(True)
    
    geo = geometry_clean(nec.get_geometry())

    wire_r = wire_diameter/2;
    helix_r = diameter/2;
    
    
    print "Wire Diameter %s" % (wire_r * 2)
    
    helix_turns = 0.5
    
    # helix loop 
    helix_twist_height = height / helix_turns
    geo.helix(tag_id=1, nr_segments=50, spacing=helix_twist_height, lenght=height, start_radius=np.array([helix_r, 0]), end_radius=np.array([helix_r, 0]), wire_radius=wire_r)
    geo.move(rotate_z=90, copies=3, tag_inc=1)
    geo.wire(tag_id=10, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([helix_r, 0, height]), radius=wire_r)
    geo.wire(tag_id=11, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([0, helix_r, height]), radius=wire_r)
    geo.wire(tag_id=12, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([-helix_r, 0, height]), radius=wire_r)
    geo.wire(tag_id=13, nr_segments=5, src=np.array([0, 0, height]), dst=np.array([0, -helix_r, height]), radius=wire_r)
    
    # Everything is copper
    nec.set_wire_conductivity(copper_conductivity)
    # finish structure definition
    nec.geometry_complete(ground_plane=False)

    # Voltage excitation at legs of the antenna
    nec.voltage_excitation(wire_tag=1, segment_nr=1, voltage=1.0 )
    nec.voltage_excitation(wire_tag=2, segment_nr=1, voltage=1.0 )
    nec.voltage_excitation(wire_tag=3, segment_nr=1, voltage=1.0 )
    nec.voltage_excitation(wire_tag=4, segment_nr=1, voltage=1.0 )
    #nec.set_frequencies_linear(start_frequency=140, stop_frequency=150, count=100)
    #nec.radiation_pattern(thetas=Range(90, 90, count=1), phis=Range(180,180,count=1))

    return nec

#antenna=sc_quad_helix(143,0.8,2*1.62100E-01)
#antenna.xq_card(0)

start = 100
stop  = 150
count = stop - start

def get_gain_swr_range(height, diameter, start=start, stop=stop, step=50):
    gains_db = []
    frequencies = []
    vswrs = []
    for freq in range(start, stop + 1, step):
        nec = sc_quad_helix(height, diameter)
        nec.set_frequency(freq) # TODO: ensure that we don't need to re-generate this!
        nec.radiation_pattern(thetas=Range(90, 90, count=1), phis=Range(180,180,count=1))

        rp = nec.context.get_radiation_pattern(0)
        ipt = nec.get_input_parameters(0)
        z = ipt.get_impedance()

        # Gains are in decibels
        gains_db.append(rp.get_gain()[0])
        vswrs.append(vswr(z, system_impedance))
        frequencies.append(ipt.get_frequency())

    return frequencies, gains_db, vswrs

def create_optimization_target():
  def target(args):
      height, diameter  = args
      if height <= 0 or diameter <= 0:
          return float('inf')

      try:
        result = 0

        vswr_score = 0
        gains_score = 0

        freqs, gains, vswrs = get_gain_swr_range(l_1, x_1, tau, start=143, stop=144)

        for gain in gains:
            gains_score += gain
        for vswr in vswrs:
            if vswr >= 1.8:
                vswr = np.exp(vswr) # a penalty :)
            vswr_score += vswr

        # VSWR should minimal in both bands, gains maximal:
        result = vswr_score - gains_score

      except:
          print "Caught exception"
          return float('inf')

      print result

      return result
  return target


def simulate_and_get_impedance(nec):
  nec.set_frequency(design_freq_mhz)

  nec.xq_card(0)

  index = 0
  return nec.get_input_parameters(index).get_impedance()

system_impedance = 50 # This makes it a bit harder to optimize, given the 75 Ohm TLs, which is good for this excercise of course...

# (2.4 GHz to 2.5 GHz) and the 5.8 GHz ISM band (5.725 GHz to 5.875 GHz)

design_freq_mhz = 143 # The center of the first range
wavelength = 299792e3/(design_freq_mhz*1000000)

majorLocator = mpl.ticker.MultipleLocator(10)
majorFormatter = mpl.ticker.FormatStrFormatter('%d')
minorLocator = mpl.ticker.MultipleLocator(1)
minorFormatter = mpl.ticker.FormatStrFormatter('%d')


def draw_frequencie_ranges(ax):
    ax.axvline(x=140, color='red', linewidth=1)
    ax.axvline(x=144, color='red', linewidth=1)

def show_report(height, diameter):
    nec = sc_quad_helix(height, diameter)

    z = simulate_and_get_impedance(nec)

    print "Initial impedance: (%6.1f,%+6.1fI) Ohms" % (z.real, z.imag)
    print "VSWR @ 50 Ohm is %6.6f" % vswr(z, 50)

    nec = sc_quad_helix(height, diameter)
  
    freqs, gains, vswrs = get_gain_swr_range(height, diameter, step=5)

    freqs = np.array(freqs) / 1000000 # In MHz
  
    ax = plt.subplot(111)
    ax.plot(freqs, gains)
    draw_frequencie_ranges(ax)

    ax.set_title("Gains of a 5-element log-periodic antenna")
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Gain")

    ax.yaxis.set_major_locator(majorLocator)
    ax.yaxis.set_major_formatter(majorFormatter)

    ax.yaxis.set_minor_locator(minorLocator)
    ax.yaxis.set_minor_formatter(minorFormatter)

    ax.yaxis.grid(b=True, which='minor', color='0.75', linestyle='-')

    plt.show()

    ax = plt.subplot(111)
    ax.plot(freqs, vswrs)
    draw_frequencie_ranges(ax)

    ax.set_yscale("log")
    ax.set_title("VSWR of a 6-element log-periodic antenna @ 50 Ohm impedance")
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("VSWR")

    ax.yaxis.set_major_locator(majorLocator)
    ax.yaxis.set_major_formatter(majorFormatter)
    ax.yaxis.set_minor_locator(minorLocator)
    ax.yaxis.set_minor_formatter(minorFormatter)
  
    ax.yaxis.grid(b=True, which='minor', color='0.75', linestyle='-')
    plt.show()


if (__name__ == '__main__'):
  initial_height  = wavelength / 2
  initial_diameter  = wavelength / 2

  print "Wavelength is %0.4fm, initial height and diameter is %0.4fm, %0.4fm" % (wavelength, initial_height, initial_diameter)
  
  print "Unoptimized antenna..."
  show_report(initial_height, initial_diameter)

  print "Optimizing antenna..."
  target = create_optimization_target()

  # Optimize local minimum only with gradient desce
  #optimized_result = scipy.optimize.minimize(target, np.array([initial_l1, initial_x1, initial_tau]), method='Nelder-Mead')

  # Use differential evolution:
  minimizer_kwargs = dict(method='Nelder-Mead')
  bounds = [ (0.01, 0.2), (0.01, 0.2), (0.7, 0.9) ]
  optimized_result = scipy.optimize.differential_evolution(target, bounds, seed=42, disp=True, popsize=20)

  # Basin hopping isn't so good, but could also have been an option:
  #optimized_result = scipy.optimize.basinhopping(target, np.array([initial_l1, initial_x1, initial_tau]), minimizer_kwargs=minimizer_kwargs, niter=5, stepsize=0.015, T=2.0, disp=True)

  print "Optimized antenna..."
  optimized_l1, optimized_x1, optimized_tau =  optimized_result.x[0], optimized_result.x[1], optimized_result.x[2]
  show_report(optimized_l1, optimized_x1, optimized_tau)


