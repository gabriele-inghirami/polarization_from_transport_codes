#!/usr/bin/env python3

import fileinput
import math
import numpy as np
import sys
import os
import os.path
import pickle
import gzip
from itertools import islice
from datetime import datetime


ids=[27,40] #urqmd itypes
names=["Lambda","Sigma0"] #hadron names
masses=[1.116,1.192] #hadron masses adopted by UrQMD

#limits for the transverse momentum
pt_min=0.1
pt_max=6.

#limits for |rapidity|
rap_lim=1.0

#we set the parameter hbarc
hbarc=0.197326

#we set how many lines of file containing the infos about the hadrons to read at once
nlines=2000000

#array of the averages
avg=np.zeros(len(ids),dtype=np.float64) #averages including all values
avg_lim=np.zeros(len(ids),dtype=np.float64) #averages forcing the abs(entry) to be 0.5 at max
avg_exc=np.zeros(len(ids),dtype=np.float64) #averages excluding the entry if its abs > 0.5

#we get the name of input and output files
N_input_files=len(sys.argv)-1

if(N_input_files!=2):
   print ('Syntax: python3 compute_mean_spin_urqmd.py <vorticity pickled file> <hadron_data_inputfile>')
   sys.exit(1)

vorfile=sys.argv[1]
hadfile=sys.argv[2]

outfiles=[]
datas=[]
ind=[]
for i,n in enumerate(names,0):
    outfiles.append(hadfile+"_"+n+"_polarization")
    datas.append(np.zeros((nlines,10),dtype=np.float64)) #one multidimensional np array for hadrons with fields: t,x,y,z,pt,rapidity,Sx,Sy,Sz,omega_zx
    ind.append(0) #counter for the accepted hadrons of the various kinds

if(vorfile[-3:]==".gz"):
    print("Opening gzipped file "+vorfile)
    vf=gzip.open(vorfile,"rb")
else:
    print("Opening file "+vorfile)
    vf=open(vorfile,"rb")
     
data=pickle.load(vf)
vf.close()

intt,inxx,inyy,inzz,invx,invy,invz,temp,omega_tx,omega_ty,omega_tz,omega_yz,omega_zx,omega_xy=data[:]

dt=intt[1]-intt[0]
dx=inxx[1]-inxx[0]
dy=inyy[1]-inyy[0]
dz=inzz[1]-inzz[0]

nt=len(intt)
nx=len(inxx)
ny=len(inyy)
nz=len(inzz)

tmin=intt[0]-dt/2.
tmax=intt[-1]+dt/2.
xmin=inxx[0]-dx/2.
xmax=inxx[-1]+dx/2.
ymin=inyy[0]-dy/2.
ymax=inyy[-1]+dy/2.
zmin=inzz[0]-dz/2.
zmax=inzz[-1]+dz/2.


try:
  if(hadfile[-3:]==".gz"):
    print("Opening gzipped file "+hadfile)
    hf=gzip.open(hadfile,"r")
  else:
    print("Opening file "+hadfile)
    hf=open(hadfile,"r")
except:
    print("Sorry, but I can't open "+hadfile+", therefore I quit.")
    sys.exit(2)

fon=[] #list of output file handlers
sp="   "
for i,n in enumerate(outfiles,0):
    if(os.path.exists(n)):
        suff=datetime.now().strftime("%A-%d-%B-%Y-%I-%M%p")
        os.rename(n,n+"_backup_"+suff) #we create a backup copy of already existing files
    fon.append(open(n,"w"))

count_reads=0
count_lines=0
n_had=len(ids)
tot_hadrons=np.zeros(n_had,dtype=np.int64) # total hadrons of a certain species
otime_orap=np.zeros(n_had,dtype=np.int64) # out of max time hadrons with rapidity beyond the limits
otime_irap=np.zeros(n_had,dtype=np.int64) # out of max time hadrons with rapidity within the limits
ospace_x_orap=np.zeros(n_had,dtype=np.int64) # out of x borders hadrons with rapidity beyond the limits
ospace_x_irap=np.zeros(n_had,dtype=np.int64) # out of x borders hadrons with rapidity within the limits
ospace_y_orap=np.zeros(n_had,dtype=np.int64) # out of y borders hadrons with rapidity beyond the limits
ospace_y_irap=np.zeros(n_had,dtype=np.int64) # out of y borders hadrons with rapidity within the limits
ospace_z_orap=np.zeros(n_had,dtype=np.int64) # out of z borders hadrons with rapidity beyond the limits
ospace_z_irap=np.zeros(n_had,dtype=np.int64) # out of z borders hadrons with rapidity within the limits
orap=np.zeros(n_had,dtype=np.int64) # hadrons within the time space box with rapidity beyond the limits
opt_low=np.zeros(n_had,dtype=np.int64) # hadrons within the space time box with rapdity within the limits, but pt < pt_min
opt_high=np.zeros(n_had,dtype=np.int64) # hadrons within the space time box with rapdity within the limits, but pt > pt_max
while(True):
    # we read the hadron data file hf in slices, each nlines long
    # the hadron file can be very long, in this way if the script is interrupted
    # some results are still printed for a preliminary analysis, while still avoiding
    # to print the results line by line, which is usually inefficient because of the
    # large number of I/O operations. On the other hand, probably the best approach
    # is to split the hadron data files in several chunckes.
    it=islice(hf,count_lines,count_lines+nlines)
    for line in it:
        count_reads=count_reads+1
        stuff=line.split()
        if(len(stuff)!=9):
            continue
        else:
            # we iterate over the hadron species of interest declared at the beginning of the file
            for el,kel in enumerate(ids,0):
                if(int(stuff[0])==kel):
                    # counter of the number of hadrons the species "kel" with index el (in all the file)
                    tot_hadrons[el]+=1
                    # counter of the number of hadrons the species "kel" with index el (within a slice)
                    ds=ind[el]
                    # mass of the selected hadron species, it is defined at the beginning of the file
                    m=masses[el]
                    t,x,y,z,Ep,px,py,pz=np.float64(stuff[1:])
                    rapidity=0.5*math.log((Ep+pz)/(Ep-pz))
                    # we count how many are the hadrons excluded because of the space-time interval in which
                    # we have data for the vorticity or because they are out of the rapidity and transverse
                    # momentum intervals
                    discarded=False
                    if(t>tmax):
                        discarded=True
                        if abs(rapidity)<rap_lim:
                            otime_irap[el]+=1
                        else:
                            otime_orap[el]+=1
                    if((x < xmin) or (x > xmax)):
                        discarded=True
                        if abs(rapidity)<rap_lim:
                            ospace_x_irap[el]+=1
                        else:
                            ospace_x_orap[el]+=1
                    if((y < ymin) or (y > ymax)):
                        discarded=True
                        if abs(rapidity)<rap_lim:
                            ospace_y_irap[el]+=1
                        else:
                            ospace_y_orap[el]+=1
                    if((z < zmin) or (z > zmax)):
                        discarded=True
                        if abs(rapidity)<rap_lim:
                            ospace_z_irap[el]+=1
                        else:
                            ospace_z_orap[el]+=1
                    if discarded:
                        continue
                    # if we are here we inside the space-time box for which we have vorticity data
                    if(abs(rapidity)>rap_lim):
                        orap[el]+=1
                        continue
                    pt=math.sqrt(px**2+py**2)
                    if(pt<pt_min):
                        opt_low[el]+=1
                        continue
                    if(pt>pt_max):
                        opt_high[el]+=1
                        continue

                    h=int(math.floor((t-tmin)/dt))
                    i=int(math.floor((x-xmin)/dx))
                    j=int(math.floor((y-ymin)/dy))
                    k=int(math.floor((z-zmin)/dz))
                    if(math.isfinite(omega_tx[h,i,j,k])):
                       otx=omega_tx[h,i,j,k]
                    else:
                       continue
                    if(math.isfinite(omega_ty[h,i,j,k])):
                       oty=omega_ty[h,i,j,k]
                    else:
                       continue
                    if(math.isfinite(omega_tz[h,i,j,k])):
                       otz=omega_tz[h,i,j,k]
                    else:
                       continue
                    if(math.isfinite(omega_yz[h,i,j,k])):
                       osx=omega_yz[h,i,j,k]
                    else:
                       continue
                    if(math.isfinite(omega_zx[h,i,j,k])):
                       osy=omega_zx[h,i,j,k]
                    else:
                       continue
                    if(math.isfinite(omega_xy[h,i,j,k])):
                       osz=omega_xy[h,i,j,k]
                    else:
                       continue
                    #we compute S in the lab frame
                    fac=1/(4*m)
                    Sx=fac*(Ep*osx+(py*otz-pz*oty))
                    Sy=fac*(Ep*osy+(pz*otx-px*otz))
                    #print("UUUUU "+str(Ep)+sp+str(osy)+sp+str(pz)+sp+str(otx)+sp+str(px)+sp+str(otz))
                    Sz=fac*(Ep*osz+(px*oty-py*otx))
                    #we boost S in the particle LRF frame
                    bof=(px*Sx+py*Sy+pz*Sz)/(Ep*(m+Ep))
                    Sx_lrf=Sx-bof*px
                    if abs(Sx_lrf)>0.5:
                        continue
                    Sy_lrf=Sy-bof*py
                    if abs(Sy_lrf)>0.5:
                        continue
                    Sz_lrf=Sz-bof*pz
                    if abs(Sz_lrf)>0.5:
                        continue

                    datas[el][ds,0:4]=np.float64(stuff[1:5])#we copy the coordinates t,x,y,z
                    datas[el][ds,4:6]=pt,rapidity
                    datas[el][ds,6:9]=Sx_lrf,Sy_lrf,Sz_lrf
                    datas[el][ds,9]=osy
                    #datas[el][ds,9]=-2*Sy_lrf # y polarization, normalized by -1/2
                    # attempt to implement the additional boost by Florkowski and others, not really useful
                    #vLx=px/Ep
                    #vLy=py/Ep
                    #vLz=pz/Ep
                    #gL=Ep/m
                    #datas[el][ds,11]=1./math.sqrt(1-vLy**2)*(-2*Sy_lrf-gL/(gL+1)*(2*(vLx*Sx_lrf+vLy*Sy_lrf+vLz*Sz_lrf)*(-vLy)))
                    ind[el]=ind[el]+1#index of the next ds-th hadron entry

    if(count_reads > nlines):
        print("Hey, something here went wrong... I counted "+str(count_lines)+" read in a block of "+hadfile+", but they should have been at most "+str(nlines))
        print("Please, check...")
        sys.exit(3)

    ff='{:12.8e}'

    # we save in the outputfiles the results of the hadron data file slice
    for i,n in enumerate(outfiles,0):
        #print("Writing "+n)
        for a in range(0,ind[i]):
            #print(str(a))
            fon[i].write(ff.format(datas[i][a,0])+sp+ff.format(datas[i][a,1])+sp+ff.format(datas[i][a,2])+sp+ff.format(datas[i][a,3])+sp+ff.format(datas[i][a,4])+sp+ff.format(datas[i][a,5]))
            for q in range(6,10):
                fon[i].write(sp+ff.format(datas[i][a,q]))
            fon[i].write("\n")
    
    # we exit from the while(True) loop
    if(count_reads < nlines):
        break
    else:
        # we increment the slice offset and we reset the counters
        count_lines=count_lines+nlines
        count_reads=0
        #print("*** Before reset we had: "+str(ind[:]))
        for i in range(len(ind)):
            ind[i]=0

for i,n in enumerate(outfiles,0):
    fon[i].close() 
hf.close()
print("All done!")
sf='{:5.3f}'
for i,n in enumerate(names):
    nh=tot_hadrons[i]/100.
    print("Total "+n+" : "+str(tot_hadrons[i]))
    print("Discarded "+n+" with t > "+str(tmax)+" fm and |rapidity| > "+str(rap_lim)+" : "+str(otime_orap[i])+" ("+sf.format(otime_orap[i]/nh)+"%)")
    print("Discarded "+n+" with t > "+str(tmax)+" fm and |rapidity| <= "+str(rap_lim)+" : "+str(otime_irap[i])+" ("+sf.format(otime_irap[i]/nh)+"%)")
    print("Discarded "+n+" with x < "+str(xmin)+" fm and x > "+str(xmax)+" fm and |rapidity| > "+str(rap_lim)+" : "+str(ospace_x_orap[i])+" ("+sf.format(ospace_x_orap[i]/nh)+"%)")
    print("Discarded "+n+" with x < "+str(xmin)+" fm and x > "+str(xmax)+" fm and |rapidity| < "+str(rap_lim)+" : "+str(ospace_x_irap[i])+" ("+sf.format(ospace_x_irap[i]/nh)+"%)")
    print("Discarded "+n+" with y < "+str(ymin)+" fm and y > "+str(ymax)+" fm and |rapidity| > "+str(rap_lim)+" : "+str(ospace_y_orap[i])+" ("+sf.format(ospace_y_orap[i]/nh)+"%)")
    print("Discarded "+n+" with y < "+str(ymin)+" fm and y > "+str(ymax)+" fm and |rapidity| < "+str(rap_lim)+" : "+str(ospace_y_irap[i])+" ("+sf.format(ospace_y_irap[i]/nh)+"%)")
    print("Discarded "+n+" with z < "+str(zmin)+" fm and z > "+str(zmax)+" fm and |rapidity| > "+str(rap_lim)+" : "+str(ospace_z_orap[i])+" ("+sf.format(ospace_z_orap[i]/nh)+"%)")
    print("Discarded "+n+" with z < "+str(zmin)+" fm and z > "+str(zmax)+" fm and |rapidity| < "+str(rap_lim)+" : "+str(ospace_z_irap[i])+" ("+sf.format(ospace_z_irap[i]/nh)+"%)")
    print("Discarded "+n+" within the space-time box because of |rapidity| > "+str(rap_lim)+" : "+str(orap[i])+" ("+sf.format(orap[i]/nh)+"%)")
    print("Discarded "+n+" within the space-time box with |rapidity| < "+str(rap_lim)+" because of pt < "+str(pt_min)+" GeV : "+str(opt_low[i])+" ("+sf.format(opt_low[i]/nh)+"%)")
    print("Discarded "+n+" within the space-time box with |rapidity| < "+str(rap_lim)+" because of pt > "+str(pt_max)+" GeV : "+str(opt_high[i])+" ("+sf.format(opt_high[i]/nh)+"%)")
