#!/usr/bin/env python3

# version 0.1.1 08/01/2022

import fileinput
import math
import numpy as np
import sys
import os
import pickle
import matplotlib
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import gzip

# we make 2D x-z plots at y=y_of_interest, for t_min<=t<=t_max 
y_of_interest=[0.]
time_min=15.00
time_max=15.00
limval=1.0 #maximum value in cbar
#vorticity_cmap = matplotlib.cm.jet
vorticity_cmap = matplotlib.cm.gnuplot

#we get the name of input and output files
N_input_files=len(sys.argv)-1

if(N_input_files!=3):
   print ('Syntax: python3 make_vorticity_plots_smash.py <pickle binary data file> <output directory> <plot common title>')
   sys.exit(1)

inputfile=sys.argv[1]
od=sys.argv[2]
common_title=sys.argv[3]
if(not os.path.exists(od)):
  os.mkdir(od)

if(inputfile[-3:]==".gz"):
    print("Opening gzipped file "+inputfile)
    infile=gzip.open(inputfile,"rb")
else:
    print("Opening file "+inputfile)
    infile=open(inputfile,"rb")

data=pickle.load(infile)
infile.close()

tt,xx,yy,zz,vx,vy,vz,temp,omega_tx,omega_ty,omega_tz,omega_yz,omega_zx,omega_xy=data[:]


yy_selected=[] #it contains the indexes of yy correponding to the z_of_interest points
ftim=[] #it keeps track if it is the first time that the slice is plotted
omxy_min_arr=[]
omyz_min_arr=[]
omzx_min_arr=[]
tempmin_arr=[]
omxy_max_arr=[]
omyz_max_arr=[]
omzx_max_arr=[]
tempmax_arr=[]

dx=xx[1]-xx[0]
dz=zz[1]-zz[0]

ny=len(yy)
if(ny<2):
  zz_selected.append(0)
  ftim.append(True)
else:
  dy=yy[1]-yy[0]
  ymin=yy[0]-dy/2.
  ymax=yy[-1]+dy/2.
  for i in range(len(y_of_interest)):
    y_test=y_of_interest[i]
    if((y_test >= ymin) and (y_test<=ymax)):
      yy_selected.append(int(math.floor((y_test-ymin)/dy)))
      ftim.append(True)
 
nysel=len(yy_selected)
if(nysel==0):
  print("No selected points are in the available y-range")
  sys.exit(1)

fig_size = plt.rcParams["figure.figsize"]
fig_size[0] = 16
fig_size[1] = 8
plt.rcParams["figure.figsize"]=fig_size


for it in range(len(tt)):
  if(tt[it]<time_min):
    continue
  if(tt[it]>time_max):
    sys.exit(0)
  print("*****\n\nDoing timestep "+str(it)+", t="+'{:4.2f}'.format(tt[it]))
  for iki in range(nysel):
    ik=yy_selected[iki]
   # if(ftim[iki]==True):
   #   ftim[iki]==False
   #   testval=max(abs(np.amin(omega_xy[:,imin:imax,ik,:])),abs(np.amax(omega_xy[:,imin:imax,ik,:])))
   #   omxy_min_arr.append(-testval)
   #   omxy_max_arr.append(testval)
   #   testval=max(abs(np.amin(omega_zx[:,imin:imax,iki,:])),abs(np.amax(omega_zx[:,imin:imax,ik,:])))
   #   omzx_min_arr.append(-testval)
   #   omzx_max_arr.append(testval)
   #   testval=max(abs(np.amin(omega_yz[:,imin:imax,ik,:])),abs(np.amax(omega_yz[:,imin:imax,ik,:])))
   #   omyz_min_arr.append(-testval)
   #   omyz_max_arr.append(testval)
   #   tempmin_arr.append(np.amin(temp[:,imin:imax,ik,:]))
   #   tempmax_arr.append(np.amax(temp[:,imin:imax,ik,:]))

    if(np.amax(temp[it,:,ik,:])>0):
      outdir=od+"/z_"+'{:+05.2f}'.format(yy[ik])
      if(not os.path.exists(outdir)):
        os.mkdir(outdir)
      print("Y slice: "+str(ik)+" ,y="+'{:4.2f}'.format(yy[ik]))

#     plots with local maxima and minima

      plt.suptitle(common_title+", t="+'{:4.2f}'.format(tt[it])+" - y="+'{:4.2f}'.format(yy[ik]))

      #maxvalue=np.nanmax(omega_zx[it,:,ik,:])
      #minvalue=np.nanmin(omega_zx[it,:,ik,:])
      #topval=max(abs(maxvalue),abs(minvalue))
      plt.subplot(121)
      #plt.imshow(omega_zx[it,:,ik,:],extent=[zz[0]-dz/2, zz[-1]+dz/2,xx[0]-dx/2,xx[-1]+dx/2], origin='lower',cmap='coolwarm',vmin=-.5,vmax=.5,aspect='equal',interpolation=None)
      plt.imshow(omega_zx[it,:,ik,:],extent=[zz[0]-dz/2, zz[-1]+dz/2,xx[0]-dx/2,xx[-1]+dx/2], origin='lower',cmap='coolwarm',vmin=-limval,vmax=limval,aspect='equal',interpolation='bilinear')
      #plt.imshow(omega_zx[it,:,ik,:],extent=[zz[0]-dz/2, zz[-1]+dz/2,xx[0]-dx/2,xx[-1]+dx/2], origin='lower',cmap='coolwarm',vmin=-limval,vmax=limval,aspect='equal',interpolation='None')
      plt.title(r"$\omega_{zx}$")
      plt.xlabel('z [fm]')
      plt.ylabel('x [fm]')
      ax=plt.gca()
      divider = make_axes_locatable(ax)
      cax = divider.append_axes("right", size="5%", pad=0.05)
      plt.colorbar(label=r'$\omega_{zx}$',cax=cax,format="%6.3f")

      plt.subplot(122)
#      masked_array = np.ma.array(temp,mask=(temp==0))
#      vorticity_cmap.set_bad('white',1.)
#      plt.imshow(masked_array[it,:,ik,:]*1000,extent=[zz[0]-dz/2, zz[-1]+dz/2,xx[0]-dx/2,xx[-1]+dx/2], origin='lower',cmap=vorticity_cmap,aspect='equal',interpolation=None)
      #plt.imshow(temp[it,:,ik,:]*1000,extent=[zz[0]-dz/2, zz[-1]+dz/2,xx[0]-dx/2,xx[-1]+dx/2], origin='lower',cmap=vorticity_cmap,aspect='equal',interpolation=None)
      plt.imshow(temp[it,:,ik,:]*1000,extent=[zz[0]-dz/2, zz[-1]+dz/2,xx[0]-dx/2,xx[-1]+dx/2], origin='lower',cmap=vorticity_cmap,aspect='equal',interpolation='bilinear')
      plt.title("Temperature")
      plt.xlabel('z [fm]')
      plt.ylabel('x [fm]')
      ax=plt.gca()
      divider = make_axes_locatable(ax)
      cax = divider.append_axes("right", size="5%", pad=0.05)
      plt.colorbar(label="T [MeV]",cax=cax,format="%6.3f")


      plt.tight_layout()

      plt.savefig(outdir+"/"+"t_"+'{:05.2f}'.format(tt[it])+".png",dpi=200,pad_inches=0.)
      plt.close('all')
    
