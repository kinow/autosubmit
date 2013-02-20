#!/bin/bash
#This is an example of the configuration file needed to run the nccf_atm_monthly_new.sh. You can copy it to the directory where you run the script. For any other information, you can look at the details of how to use this file or the nccf_atm_monthly_new in the cfu wiki
INSTITUTION="IC3"
SOURCE="EC-Earth2.3.0"
LEVEL_LST=(92500,85000,70000,50000,20000,10000,5000)
DATADIR="/cfunas/exp/ecearth"  #where MMA files located
SAVEDIR="/cfunas/exp/ecearth"  # for Saving outputs
HEAD_DIR="/cfu/pub/scripts/postp_ecearth/header" # some of the header information
WORKDIR="/scratch/$USER/pp/nccf_atm_monthly_$$"
NFRP=3 # ecearth output frequency (hours), this is for computing the accumulated precipitation and flux variables
FACTOR=$((NFRP*3600)) 
EXPID=i024
SDATE=19800201
LEAD_LIST=(1980 02 1982 02 12) #lead times to be treated (1st_year 1st_month last_year last_month chunk_size(in months)
MEM_LST=(fc2)
VAR_LST_2D=() #T2M D2M SSTK MSL PRECIP SSR STR TTR TSR TSRC TTRC SLHF SSHF U10M V10M SSRD CP SF E SSRU SSRC STRU STRD TCC # list of 2D variables to be processed (if left blank, the script will automatically look for the variables present in the files and treat them all)
VAR_LST_3D=() # T U V Z Q W CC CIWC CLWC
MASK_PATH=/cfunas/exp/ecearth/land_sea_mask_320x160.nc # path of the mask for the actual resolution (used to change tos from 0 to NaN on the continents)
