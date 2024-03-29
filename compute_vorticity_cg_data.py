#!/usr/bin/env python3

# 15/08/2022

#this version has been tested with files generated by store_cgnew_v2.1.1.py

import fileinput
import math
import numpy as np
import sys
import os
import pickle
import gzip
from scipy.interpolate import interpn

"""It computes the vorticity from the data produced by store_cg.py (v. 2.1), also if gzipped."""

#it chooses whether to use standard (False) or the anisotropy corrected (True) energy density
use_aniso=False

der_type = 2 #1 = numpy derivatives, 2 = 2nd order centered differences with 1st at borders

temp_limit = 0.0005 # temperature limit to accept a cell in GeV for derivative computation

#we set the parameter hbarc
hbarc=0.197326

#enable the linear interpolation of empty cells (only in space)
enable_smooth=True


#we get the name of input and output files
N_input_files=len(sys.argv)-1

if(N_input_files!=2):
   print ('Syntax: python3 compute_vorticity_cg_data.py <inputfile pickled file> <outputfile>')
   sys.exit(1)

inputfile=sys.argv[1]
outputfile=sys.argv[2]

if(inputfile[-3:]==".gz"):
    print("Opening gzipped file "+inputfile)
    pi=gzip.open(inputfile,"rb")
else:
    print("Opening file "+inputfile)
    pi=open(inputfile,"rb")
     
data=pickle.load(pi)

# we get the data from the tuple read from the pickle archive
intt,inxx,inyy,inzz,invx,invy,invz,inrho,inen,inmuSTD,intempSTD,inmuANI,intempANI,ptra,ppar,num_had,pressSTD,sSTD,pressANI,sANI,rho_bab=data[:]

dt=intt[1]-intt[0]
dx=inxx[1]-inxx[0]
dy=inyy[1]-inyy[0]
dz=inzz[1]-inzz[0]

nt=len(intt)
nx=len(inxx)
ny=len(inyy)
nz=len(inzz)

# this function replaces the value of a cell with the average values of the cells in the surroundig cube
def smooth_down(array,i,j,k):
    tot=0
    p=0
    for l in range(max(i-1,0),min(i+1,nx)):
        for m in range(max(j-1,0),min(j+1,ny)): 
            for n in range(max(k-1,0),min(k+1,nz)):
                tot=tot+array[l,m,n]
                p=p+1.
    if p!=0:
        return tot/p
    else:
        return 0.

if(use_aniso):
    print("Use temperature with anisotropic correction")
    temp=intempANI
else:
    print("Use standard temperature, without anisotropic correction")
    temp=intempSTD
                         

# the gamma Lorentz factor
glf=1/np.sqrt(1-invx**2-invy**2-invz**2)

#old_settings=np.seterr(divide='ignore',invalid='ignore') #seterr sets the new values and returns the old settings
#with np.errstate(divide='ignore', invalid='ignore'):

bt=np.zeros(temp.shape,dtype=np.float64)
bx=np.zeros(temp.shape,dtype=np.float64)
by=np.zeros(temp.shape,dtype=np.float64)
bz=np.zeros(temp.shape,dtype=np.float64)


for h in range(nt):
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                if(temp[h,i,j,k]>0):
                    bt[h,i,j,k]=glf[h,i,j,k]/temp[h,i,j,k]
                    #we are using the covariant components, index down, so they get a -1 sign (Minkowski metric signature +---)
                    bx[h,i,j,k]=-invx[h,i,j,k]*glf[h,i,j,k]/temp[h,i,j,k]
                    by[h,i,j,k]=-invy[h,i,j,k]*glf[h,i,j,k]/temp[h,i,j,k]
                    bz[h,i,j,k]=-invz[h,i,j,k]*glf[h,i,j,k]/temp[h,i,j,k]

if(enable_smooth):
    bt_fixed=np.zeros_like(bt)
    bx_fixed=np.zeros_like(bx)
    by_fixed=np.zeros_like(by)
    bz_fixed=np.zeros_like(bz)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(temp[h,i,j,k]<temp_limit):
                        bt_fixed[h,i,j,k]=smooth_down(bt[h,:,:,:],i,j,k)  
                        bx_fixed[h,i,j,k]=smooth_down(bx[h,:,:,:],i,j,k)  
                        by_fixed[h,i,j,k]=smooth_down(by[h,:,:,:],i,j,k)  
                        bz_fixed[h,i,j,k]=smooth_down(bz[h,:,:,:],i,j,k)  
    bt=bt_fixed
    bx=bx_fixed
    by=by_fixed
    bz=bz_fixed


if der_type == 1:

    dbt_dx=np.gradient(bt,dx,axis=1)
    dbt_dy=np.gradient(bt,dy,axis=2)
    dbt_dz=np.gradient(bt,dz,axis=3)
    dbx_dt=np.gradient(bx,dt,axis=0)
    dby_dt=np.gradient(by,dt,axis=0)
    dbz_dt=np.gradient(bz,dt,axis=0)

    dbx_dy=np.gradient(bx,dy,axis=2)
    dbx_dz=np.gradient(bx,dz,axis=3)
    dby_dx=np.gradient(by,dx,axis=1)
    dby_dz=np.gradient(by,dz,axis=3)
    dbz_dx=np.gradient(bz,dx,axis=1)
    dbz_dy=np.gradient(bz,dy,axis=2)


elif der_type == 2:

    dbt_dx=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(i==0):
                        if((bt[h,0,j,k]!=0) and (bt[h,1,j,k]!=0)):
                            dbt_dx[h,0,j,k]=(bt[h,1,j,k]-bt[h,0,j,k])/dx
                    elif(i==nx-1):
                        if((bt[h,nx-1,j,k]!=0) and (bt[h,nx-2,j,k]!=0)):
                            dbt_dx[h,nx-1,j,k]=(bt[h,nx-1,j,k]-bt[h,nx-2,j,k])/dx
                    elif((bt[h,i-1,j,k]!=0) and (bt[h,i+1,j,k]!=0)):
                        dbt_dx[h,i,j,k]=(bt[h,i+1,j,k]-bt[h,i-1,j,k])/(2*dx)
                    elif((bt[h,i-1,j,k]!=0) and (bt[h,i,j,k]!=0)):
                        dbt_dx[h,i,j,k]=(bt[h,i,j,k]-bt[h,i-1,j,k])/(dx)
                    elif((bt[h,i+1,j,k]!=0) and (bt[h,i,j,k]!=0)):
                        dbt_dx[h,i,j,k]=(bt[h,i+1,j,k]-bt[h,i,j,k])/(dx)

    dbt_dy=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(j==0):
                        if((bt[h,i,0,k]!=0) and (bt[h,i,1,k]!=0)):
                            dbt_dy[h,i,0,k]=(bt[h,i,1,k]-bt[h,i,0,k])/dy
                    elif(j==ny-1):
                        if((bt[h,i,ny-1,k]!=0) and (bt[h,i,ny-2,k]!=0)):
                            dbt_dy[h,i,ny-1,k]=(bt[h,i,ny-1,k]-bt[h,i,ny-2,k])/dy
                    elif((bt[h,i,j-1,k]!=0) and (bt[h,i,j+1,k]!=0)):
                        dbt_dy[h,i,j,k]=(bt[h,i,j+1,k]-bt[h,i,j-1,k])/(2*dy)
                    elif((bt[h,i,j-1,k]!=0) and (bt[h,i,j,k]!=0)):
                        dbt_dy[h,i,j,k]=(bt[h,i,j,k]-bt[h,i,j-1,k])/(dy)
                    elif((bt[h,i,j+1,k]!=0) and (bt[h,i,j,k]!=0)):
                        dbt_dy[h,i,j,k]=(bt[h,i,j+1,k]-bt[h,i,j,k])/(dy)

    dbt_dz=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(k==0):
                        if((bt[h,i,j,0]!=0) and (bt[h,i,j,1]!=0)):
                            dbt_dz[h,i,j,0]=(bt[h,i,j,1]-bt[h,i,j,0])/dz
                    elif(k==nz-1):
                        if((bt[h,i,j,nz-1]!=0) and (bt[h,i,j,nz-2]!=0)):
                            dbt_dz[h,i,j,nz-1]=(bt[h,i,j,nz-1]-bt[h,i,j,nz-2])/dz
                    elif((bt[h,i,j,k-1]!=0) and (bt[h,i,j,k+1]!=0)):
                        dbt_dz[h,i,j,k]=(bt[h,i,j,k+1]-bt[h,i,j,k-1])/(2*dz)
                    elif((bt[h,i,j,k-1]!=0) and (bt[h,i,j,k]!=0)):
                        dbt_dz[h,i,j,k]=(bt[h,i,j,k]-bt[h,i,j,k-1])/(dz)
                    elif((bt[h,i,j,k+1]!=0) and (bt[h,i,j,k]!=0)):
                        dbt_dz[h,i,j,k]=(bt[h,i,j,k+1]-bt[h,i,j,k])/(dz)

    dbx_dt=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(h==0):
                        if((bx[0,i,j,k]!=0) and (bx[1,i,j,k]!=0)):
                            dbx_dt[0,i,j,k]=(bx[1,i,j,k]-bx[0,i,j,k])/dt
                    elif(h==nt-1):
                        if((bx[nt-1,i,j,k]!=0) and (bx[nt-2,i,j,k]!=0)):
                            dbx_dt[nt-1,i,j,k]=(bx[nt-1,i,j,k]-bx[nt-2,i,j,k])/dt
                    elif((bx[h-1,i,j,k]!=0) and (bx[h+1,i,j,k]!=0)):
                        dbx_dt[h,i,j,k]=(bx[h+1,i,j,k]-bx[h-1,i,j,k])/(2*dt)
                    elif((bx[h-1,i,j,k]!=0) and (bx[h,i,j,k]!=0)):
                        dbx_dt[h,i,j,k]=(bx[h,i,j,k]-bx[h-1,i,j,k])/(dt)
                    elif((bx[h+1,i,j,k]!=0) and (bx[h,i,j,k]!=0)):
                        dbx_dt[h,i,j,k]=(bx[h+1,i,j,k]-bx[h,i,j,k])/(dt)


    dby_dt=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(h==0):
                        if((by[0,i,j,k]!=0) and (by[1,i,j,k]!=0)):
                            dby_dt[0,i,j,k]=(by[1,i,j,k]-by[0,i,j,k])/dt
                    elif(h==nt-1):
                        if((by[nt-1,i,j,k]!=0) and (by[nt-2,i,j,k]!=0)):
                            dby_dt[nt-1,i,j,k]=(by[nt-1,i,j,k]-by[nt-2,i,j,k])/dt
                    elif((by[h-1,i,j,k]!=0) and (by[h+1,i,j,k]!=0)):
                        dby_dt[h,i,j,k]=(by[h+1,i,j,k]-by[h-1,i,j,k])/(2*dt)
                    elif((by[h-1,i,j,k]!=0) and (by[h,i,j,k]!=0)):
                        dby_dt[h,i,j,k]=(by[h,i,j,k]-by[h-1,i,j,k])/(dt)
                    elif((by[h+1,i,j,k]!=0) and (by[h,i,j,k]!=0)):
                        dby_dt[h,i,j,k]=(by[h+1,i,j,k]-by[h,i,j,k])/(dt)


    dbz_dt=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(h==0):
                        if((bz[0,i,j,k]!=0) and (bz[1,i,j,k]!=0)):
                            dbz_dt[0,i,j,k]=(bz[1,i,j,k]-bz[0,i,j,k])/dt
                    elif(h==nt-1):
                        if((bz[nt-1,i,j,k]!=0) and (bz[nt-2,i,j,k]!=0)):
                            dbz_dt[nt-1,i,j,k]=(bz[nt-1,i,j,k]-bz[nt-2,i,j,k])/dt
                    elif((bz[h-1,i,j,k]!=0) and (bz[h+1,i,j,k]!=0)):
                        dbz_dt[h,i,j,k]=(bz[h+1,i,j,k]-bz[h-1,i,j,k])/(2*dt)
                    elif((bz[h-1,i,j,k]!=0) and (bz[h,i,j,k]!=0)):
                        dbz_dt[h,i,j,k]=(bz[h,i,j,k]-bz[h-1,i,j,k])/(dt)
                    elif((bz[h+1,i,j,k]!=0) and (bz[h,i,j,k]!=0)):
                        dbz_dt[h,i,j,k]=(bz[h+1,i,j,k]-bz[h,i,j,k])/(dt)


    dbx_dy=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(j==0):
                        if((bx[h,i,0,k]!=0) and (bx[h,i,1,k]!=0)):
                            dbx_dy[h,i,0,k]=(bx[h,i,1,k]-bx[h,i,0,k])/dy
                    elif(j==ny-1):
                        if((bx[h,i,ny-1,k]!=0) and (bx[h,i,ny-2,k]!=0)):
                            dbx_dy[h,i,ny-1,k]=(bx[h,i,ny-1,k]-bx[h,i,ny-2,k])/dy
                    elif((bx[h,i,j-1,k]!=0) and (bx[h,i,j+1,k]!=0)):
                        dbx_dy[h,i,j,k]=(bx[h,i,j+1,k]-bx[h,i,j-1,k])/(2*dy)
                    elif((bx[h,i,j-1,k]!=0) and (bx[h,i,j,k]!=0)):
                        dbx_dy[h,i,j,k]=(bx[h,i,j,k]-bx[h,i,j-1,k])/(dy)
                    elif((bx[h,i,j+1,k]!=0) and (bx[h,i,j,k]!=0)):
                        dbx_dy[h,i,j,k]=(bx[h,i,j+1,k]-bx[h,i,j,k])/(dy)


    dbz_dy=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(j==0):
                        if((bz[h,i,0,k]!=0) and (bz[h,i,1,k]!=0)):
                            dbz_dy[h,i,0,k]=(bz[h,i,1,k]-bz[h,i,0,k])/dy
                    elif(j==ny-1):
                        if((bz[h,i,ny-1,k]!=0) and (bz[h,i,ny-2,k]!=0)):
                            dbz_dy[h,i,ny-1,k]=(bz[h,i,ny-1,k]-bz[h,i,ny-2,k])/dy
                    elif((bz[h,i,j-1,k]!=0) and (bz[h,i,j+1,k]!=0)):
                        dbz_dy[h,i,j,k]=(bz[h,i,j+1,k]-bz[h,i,j-1,k])/(2*dy)
                    elif((bz[h,i,j-1,k]!=0) and (bz[h,i,j,k]!=0)):
                        dbz_dy[h,i,j,k]=(bz[h,i,j,k]-bz[h,i,j-1,k])/(dy)
                    elif((bz[h,i,j+1,k]!=0) and (bz[h,i,j,k]!=0)):
                        dbz_dy[h,i,j,k]=(bz[h,i,j+1,k]-bz[h,i,j,k])/(dy)


    dby_dx=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(i==0):
                        if((by[h,0,j,k]!=0) and (by[h,1,j,k]!=0)):
                            dby_dx[h,0,j,k]=(by[h,1,j,k]-by[h,0,j,k])/dx
                    elif(i==nx-1):
                        if((by[h,nx-1,j,k]!=0) and (by[h,nx-2,j,k]!=0)):
                            dby_dx[h,nx-1,j,k]=(by[h,nx-1,j,k]-by[h,nx-2,j,k])/dx
                    elif((by[h,i-1,j,k]!=0) and (by[h,i+1,j,k]!=0)):
                        dby_dx[h,i,j,k]=(by[h,i+1,j,k]-by[h,i-1,j,k])/(2*dx)
                    elif((by[h,i-1,j,k]!=0) and (by[h,i,j,k]!=0)):
                        dby_dx[h,i,j,k]=(by[h,i,j,k]-by[h,i-1,j,k])/(dx)
                    elif((by[h,i+1,j,k]!=0) and (by[h,i,j,k]!=0)):
                        dby_dx[h,i,j,k]=(by[h,i+1,j,k]-by[h,i,j,k])/(dx)

    dbz_dx=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(i==0):
                        if((bz[h,0,j,k]!=0) and (bz[h,1,j,k]!=0)):
                            dbz_dx[h,0,j,k]=(bz[h,1,j,k]-bz[h,0,j,k])/dx
                    elif(i==nx-1):
                        if((bz[h,nx-1,j,k]!=0) and (bz[h,nx-2,j,k]!=0)):
                            dbz_dx[h,nx-1,j,k]=(bz[h,nx-1,j,k]-bz[h,nx-2,j,k])/dx
                    elif((bz[h,i-1,j,k]!=0) and (bz[h,i+1,j,k]!=0)):
                        dbz_dx[h,i,j,k]=(bz[h,i+1,j,k]-bz[h,i-1,j,k])/(2*dx)
                    elif((bz[h,i-1,j,k]!=0) and (bz[h,i,j,k]!=0)):
                        dbz_dx[h,i,j,k]=(bz[h,i,j,k]-bz[h,i-1,j,k])/(dx)
                    elif((bz[h,i+1,j,k]!=0) and (bz[h,i,j,k]!=0)):
                        dbz_dx[h,i,j,k]=(bz[h,i+1,j,k]-bz[h,i,j,k])/(dx)

    dby_dz=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(k==0):
                        if((by[h,i,j,0]!=0) and (by[h,i,j,1]!=0)):
                            dby_dz[h,i,j,0]=(by[h,i,j,1]-by[h,i,j,0])/dz
                    elif(k==nz-1):
                        if((by[h,i,j,nz-1]!=0) and (by[h,i,j,nz-2]!=0)):
                            dby_dz[h,i,j,nz-1]=(by[h,i,j,nz-1]-by[h,i,j,nz-2])/dz
                    elif((by[h,i,j,k-1]!=0) and (by[h,i,j,k+1]!=0)):
                        dby_dz[h,i,j,k]=(by[h,i,j,k+1]-by[h,i,j,k-1])/(2*dz)
                    elif((by[h,i,j,k-1]!=0) and (by[h,i,j,k]!=0)):
                        dby_dz[h,i,j,k]=(by[h,i,j,k]-by[h,i,j,k-1])/(dz)
                    elif((by[h,i,j,k+1]!=0) and (by[h,i,j,k]!=0)):
                        dby_dz[h,i,j,k]=(by[h,i,j,k+1]-by[h,i,j,k])/(dz)

    dbx_dz=np.zeros(temp.shape,dtype=np.float64)
    for h in range(nt):
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    if(k==0):
                        if((bx[h,i,j,0]!=0) and (bx[h,i,j,1]!=0)):
                            dbx_dz[h,i,j,0]=(bx[h,i,j,1]-bx[h,i,j,0])/dz
                    elif(k==nz-1):
                        if((bx[h,i,j,nz-1]!=0) and (bx[h,i,j,nz-2]!=0)):
                            dbx_dz[h,i,j,nz-1]=(bx[h,i,j,nz-1]-bx[h,i,j,nz-2])/dz
                    elif((bx[h,i,j,k-1]!=0) and (bx[h,i,j,k+1]!=0)):
                        dbx_dz[h,i,j,k]=(bx[h,i,j,k+1]-bx[h,i,j,k-1])/(2*dz)
                    elif((bx[h,i,j,k-1]!=0) and (bx[h,i,j,k]!=0)):
                        dbx_dz[h,i,j,k]=(bx[h,i,j,k]-bx[h,i,j,k-1])/(dz)
                    elif((bx[h,i,j,k+1]!=0) and (bx[h,i,j,k]!=0)):
                        dbx_dz[h,i,j,k]=(bx[h,i,j,k+1]-bx[h,i,j,k])/(dz)
else:
    print("Error, method to compute derivative unknown...")
    sys.exit(2)

omega_tx=0.5*hbarc*(dbt_dx-dbx_dt)
omega_ty=0.5*hbarc*(dbt_dy-dby_dt)
omega_tz=0.5*hbarc*(dbt_dz-dbz_dt)

omega_yz=0.5*hbarc*(dby_dz-dbz_dy)
omega_zx=0.5*hbarc*(dbz_dx-dbx_dz)
omega_xy=0.5*hbarc*(dbx_dy-dby_dx)

with open(outputfile,"wb") as po:
     pickle.dump((intt,inxx,inyy,inzz,invx,invy,invz,temp,omega_tx,omega_ty,omega_tz,omega_yz,omega_zx,omega_xy),po)
with open(outputfile+"_gradients","wb") as po:
     pickle.dump((intt,inxx,inyy,inzz,invx,invy,invz,temp,bt,bx,by,bz,dbt_dx,dbt_dy,dbt_dz,dbx_dt,dby_dt,dbz_dt,dbx_dy,dbx_dz,dby_dx,dby_dz,dbz_dx,dbz_dy),po)
print("All done.")
