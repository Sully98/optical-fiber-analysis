# report day of week, will just run if it is
# the day of the week specified and there is not
# already a report with the same date 
import datetime as dt
import argparse
import time
import os
import sys
from matplotlib.cbook import report_memory
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json

#======================================================================#
## plot parameters
hist_bins = 40                  # histogram bin counts
lw_grid = 0.5                   # grid linewidth
fig_dpi = 800                   # save figure's resolution

colorstyle = ['#00FFFF', '#7FFFD4', '#F0FFFF', '#F5F5DC', '#000000', '#0000FF', '#A52A2A', '#7FFF00',\
                '#D2691E', '#FF7F50', '#DC143C', '#00008B', '#006400', '#FF00FF', '#FFD700', '#DAA520',\
                '#008000', '#808080', '#4B0082', '#FFFFF0', '#F0E68C', '#E6E6FA', '#ADD8E6', '#90EE90',\
                '#00FF00', '#800000', '#000080', '#808000', '#FFA500', '#FF4500', '#DA70D6', '#FFC0CB',\
                '#DDA0DD', '#800080', '#FF0000', '#FA8072', '#A0522D', '#C0C0C0', '#D2B48C', '#008080',\
                '#13EAC9', '#069AF3', '#E6DAA6', '#0343DF', '#653700', '#C1F80A', '#3D1C02', '#FC5A50',\
                '#8C000F', '#030764', '#054907', '#ED0DD9', '#DBB40C', '#FAC205', '#15B01A', '#929591',\
                '#380280', '#FFFFCB', '#AAA662', '#C79FEF', '#7BC8F6', '#76FF7B', '#AAFF32', '#C20078']

#========================================================================#

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dow", default="M", help="Run the report on this day of week, choices are: ['M','T','W','Th','F','Sat','Sun']")
    parser.add_argument("--dir", default="./", help="Directory to look for data, default is current directory")
    parser.add_argument("--days", default="60", help="How many days should the report contain",type = int)
    parser.add_argument("--rr", default="60", help="Refresh Rate in seconds, default is 60",type = int)
    parser.add_argument("--sing_chan", default='5', help="Single channel to plot all statistics separately", type = int)
    args = parser.parse_args()
    
    day_tuples = {'M':0,'T':1,'W':2,'Th':3,'F':4,'Sat':5,'Sun':6}
    if args.dow in ['M','T','W','Th','F','Sat','Sun']:
        dow_preference = args.dow
        while True:
            if dt.datetime.now().weekday() == day_tuples[dow_preference]:
                
                last_date = dt.datetime.now()-dt.timedelta(days = args.days)
                
                dirlist = []
                dir_n = 0
                report_was_written_today = False
                for root, dirs, files in os.walk(args.dir):
                    for dir in dirs:
                        print(dir)
                        if dir.startswith("Waveform_parameter_"):
                            if dt.datetime.strptime(dir[-8:],'%Y%m%d') >= last_date:
                                dirlist.append(dir)
                                dir_n+=1
                    dirlist = sorted(dirlist,  key=lambda x: x[-8:])
                    #Check if there was a report from the same date
                    for f in files:
                        if f.startswith("status_report_"):
                            if f.split("_")[-1].split('.')[0] == dirlist[-1][-8]:
                                report_was_written_today = True
                    

                print("There are %s days of data to look at"%(dir_n))    
                if not report_was_written_today:
                    # each channel gets their own df 
                    # each df gets filled with every row of data directly from the 
                    # processed data files then we can use groupby to get what we
                    # need such as average of each day or run further analysis 
                    
                    # total plots
                    mu_fig, mu_ax = plt.subplots(1, 1, figsize=(4, 7), sharex=True)        
                    sig_fig, sig_ax = plt.subplots(1, 1, figsize=(4, 7), sharex=True)        
                    peak_fig, peak_ax = plt.subplots(1, 1, figsize=(4, 7), sharex=True)        
                    pow_fig, pow_ax = plt.subplots(1, 1, figsize=(4, 7), sharex=True)        
                    
                    # small individual plots
                    ind_mu_fig, ind_mu_ax = plt.subplots(16, 4, figsize=(10, 12), sharex=True)        
                    ind_sig_fig, ind_sig_ax = plt.subplots(16, 4, figsize=(10, 12), sharex=True)        
                    ind_peak_fig, ind_peak_ax = plt.subplots(16, 4, figsize=(10, 12), sharex=True)        
                    ind_pow_fig, ind_pow_ax = plt.subplots(16, 4, figsize=(10, 12), sharex=True)        
                    
                    # single figure highlighting 1 channel

                    sing_chan_fig, sing_chan_ax = plt.subplots(4, 1, figsize=(10, 12),sharex=True)
                    reports = []
                    alert_file = open('alert_params.json')
                    alerts = json.load(alert_file)
                    for i in range(64):
                        
                        # initialize df
                        full_df = pd.DataFrame()
                        # read through every directory, each directory is a day of data
                        for dir in dirlist:
                            # read in data and concatenate to the full df
                            day_df = pd.read_csv(args.dir+dir+"/Channel%s_out_parameter.txt"%(i),header=0, delimiter=r"\s+")
                            full_df = pd.concat([full_df,day_df])
                        # convert string times to datetime objects
                        full_df['timestamp'] = pd.to_datetime(full_df.date)
                        full_df = full_df.set_index(["timestamp"])
                        # take the average of each daily value
                        sampled_df = full_df.resample('D').mean()
                        
                        # add moving average to all values so we can add an upper and lower limit
                        sampled_df['mu_MA'] = sampled_df['mu'].rolling(window=7).mean()
                        sampled_df['mu_MA_up_lim'] = sampled_df['mu_MA'] + alerts["alert"][i]["mu_lim"]
                        sampled_df['mu_MA_low_lim'] = sampled_df['mu_MA'] - alerts["alert"][i]["mu_lim"]
                        sampled_df['mu_outside'] = np.where(((sampled_df['mu'] > sampled_df['mu_MA_up_lim']) | (sampled_df['mu'] < sampled_df['mu_MA_low_lim'])),1,0)

                        sampled_df['sig_MA'] = sampled_df['sigma'].rolling(window=7).mean()
                        sampled_df['sig_MA_up_lim'] = sampled_df['sig_MA'] + alerts["alert"][i]["sig_lim"]
                        sampled_df['sig_MA_low_lim'] = sampled_df['sig_MA'] - alerts["alert"][i]["sig_lim"]
                        sampled_df['sig_outside'] = np.where(((sampled_df['sigma'] > sampled_df['sig_MA_up_lim']) | (sampled_df['sigma'] < sampled_df['sig_MA_low_lim'])),1,0)

                        sampled_df['wave_MA'] = sampled_df['peak_wavelength'].rolling(window=7).mean()
                        sampled_df['wave_MA_up_lim'] = sampled_df['wave_MA'] + alerts["alert"][i]["wavelength_lim"]
                        sampled_df['wave_MA_low_lim'] = sampled_df['wave_MA'] - alerts["alert"][i]["wavelength_lim"]
                        sampled_df['wave_outside'] = np.where(((sampled_df['peak_wavelength'] > sampled_df['wave_MA_up_lim']) | (sampled_df['peak_wavelength'] < sampled_df['wave_MA_low_lim'])),1,0)

                        sampled_df['pow_MA'] = sampled_df['peak_power'].rolling(window=7).mean()
                        sampled_df['pow_MA_up_lim'] = sampled_df['pow_MA'] + alerts["alert"][i]["pow_lim"]
                        sampled_df['pow_MA_low_lim'] = sampled_df['pow_MA'] - alerts["alert"][i]["pow_lim"]
                        sampled_df['pow_outside'] = np.where(((sampled_df['peak_power'] > sampled_df['pow_MA_up_lim']) | (sampled_df['peak_power'] < sampled_df['pow_MA_low_lim'])),1,0)
                        
                        sampled_df.to_csv("test.csv")
                        # plot wavefrom mu, total
                        mu_ax.plot(sampled_df.index.values,  sampled_df['mu'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        mu_ax.set_ylabel("wavelength (nm)", family="Times New Roman", fontsize=8)
                        mu_ax.set_ylim(842, 854)
                        mu_ax.tick_params(axis='y', labelsize=8)
                        mu_ax.tick_params(axis='x', labelsize=8, rotation=45)   
                        mu_ax.minorticks_on()
                        mu_ax.tick_params(which='minor', width=0.5)  
                        mu_ax.legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        mu_fig.suptitle('Waveform $\mu$')
                        mu_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        # plot wavefrom mu, individual
                        if i < 16:
                            x = i
                            y = 0
                        elif i < 32:
                            x = i - 16
                            y = 1
                        elif i < 48:
                            x = i - 32
                            y = 2
                        elif i < 64:
                            x = i - 48
                            y = 3
                        ind_mu_ax[x][y].plot(sampled_df.index.values,  sampled_df['mu'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        ind_mu_ax[x][y].plot(sampled_df.index.values,  sampled_df['mu_MA'].values)
                        ind_mu_ax[x][y].plot(sampled_df.index.values,  sampled_df['mu_MA_up_lim'].values)
                        ind_mu_ax[x][y].plot(sampled_df.index.values,  sampled_df['mu_MA_low_lim'].values)
                        ind_mu_ax[x][y].set_ylim(842, 854)
                        ind_mu_ax[x][y].tick_params(axis='y', labelsize=8)
                        ind_mu_ax[x][y].tick_params(axis='x', labelsize=8, rotation=45)   
                        ind_mu_ax[x][y].minorticks_on()
                        ind_mu_ax[x][y].tick_params(which='minor', width=0.5)  
                        #ind_mu_ax[x][y].legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        ind_mu_fig.supylabel("wavelength (nm)", family="Times New Roman", fontsize=8)
                        ind_mu_fig.suptitle('Waveform $\mu$')
                        ind_mu_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        
                        # plot sigma
                        sig_ax.plot(sampled_df.index.values,  sampled_df['sigma'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        sig_ax.set_ylabel("wavelength", family="Times New Roman", fontsize=8)
                        sig_ax.set_ylim(0, 5)
                        sig_ax.tick_params(axis='y', labelsize=8)
                        sig_ax.tick_params(axis='x', labelsize=8, rotation=45)   
                        sig_ax.minorticks_on()
                        sig_ax.tick_params(which='minor', width=0.5)  
                        sig_ax.legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        sig_fig.suptitle('Waveform $\sigma$')
                        sig_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        # ind sigma 
                        ind_sig_ax[x][y].plot(sampled_df.index.values,  sampled_df['sigma'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        ind_sig_ax[x][y].plot(sampled_df.index.values,  sampled_df['sig_MA'].values)
                        ind_sig_ax[x][y].plot(sampled_df.index.values,  sampled_df['sig_MA_up_lim'].values)
                        ind_sig_ax[x][y].plot(sampled_df.index.values,  sampled_df['sig_MA_low_lim'].values)
                        ind_sig_ax[x][y].set_ylim(0,5)
                        ind_sig_ax[x][y].tick_params(axis='y', labelsize=8)
                        ind_sig_ax[x][y].tick_params(axis='x', labelsize=8, rotation=45)   
                        ind_sig_ax[x][y].minorticks_on()
                        ind_sig_ax[x][y].tick_params(which='minor', width=0.5)  
                        #ind_sig_ax[x][y].legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        ind_sig_fig.supylabel("$\sigma$", family="Times New Roman", fontsize=12)
                        ind_sig_fig.suptitle('Waveform $\sigma$', family="Times New Roman", fontsize=12)
                        ind_sig_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        ## wavelenth at peak
                        peak_ax.plot(sampled_df.index.values,  sampled_df['peak_wavelength'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        peak_ax.set_ylabel("wavelength (nm)", family="Times New Roman", fontsize=8)
                        peak_ax.set_ylim(842, 854)
                        peak_ax.tick_params(axis='y', labelsize=8)
                        peak_ax.tick_params(axis='x', labelsize=8, rotation=45)   
                        peak_ax.minorticks_on()
                        peak_ax.tick_params(which='minor', width=0.5)  
                        peak_ax.legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        peak_fig.suptitle('Wavelength at peak')
                        peak_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        # ind wavelength at peak 
                        ind_peak_ax[x][y].plot(sampled_df.index.values,  sampled_df['peak_wavelength'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        ind_peak_ax[x][y].plot(sampled_df.index.values,  sampled_df['wave_MA'].values)
                        ind_peak_ax[x][y].plot(sampled_df.index.values,  sampled_df['wave_MA_up_lim'].values)
                        ind_peak_ax[x][y].plot(sampled_df.index.values,  sampled_df['wave_MA_low_lim'].values)
                        ind_peak_ax[x][y].set_ylim(842, 854)
                        ind_peak_ax[x][y].tick_params(axis='y', labelsize=8)
                        ind_peak_ax[x][y].tick_params(axis='x', labelsize=8, rotation=45)   
                        ind_peak_ax[x][y].minorticks_on()
                        ind_peak_ax[x][y].tick_params(which='minor', width=0.5)  
                        #ind_peak_ax[x][y].legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        ind_peak_fig.supylabel("wavelength (nm)", family="Times New Roman", fontsize=12)
                        ind_peak_fig.suptitle('Wavelength at peak', family="Times New Roman", fontsize=12)
                        ind_peak_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        ## power at peak
                        pow_ax.plot(sampled_df.index.values,  sampled_df['peak_power'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        pow_ax.set_ylabel("Power (dBm)", family="Times New Roman", fontsize=8)
                        pow_ax.set_ylim(-30, -5)
                        pow_ax.tick_params(axis='y', labelsize=8)
                        pow_ax.tick_params(axis='x', labelsize=8, rotation=45)   
                        pow_ax.minorticks_on()
                        pow_ax.tick_params(which='minor', width=0.5)  
                        pow_ax.legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        pow_fig.suptitle('Power at peak')
                        pow_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        # ind power at peak 
                        ind_pow_ax[x][y].plot(sampled_df.index.values,  sampled_df['peak_power'].values, color=colorstyle[i], linewidth=0.6, label="CH%d"%i)
                        ind_pow_ax[x][y].plot(sampled_df.index.values,  sampled_df['pow_MA'].values)
                        ind_pow_ax[x][y].plot(sampled_df.index.values,  sampled_df['pow_MA_up_lim'].values)
                        ind_pow_ax[x][y].plot(sampled_df.index.values,  sampled_df['pow_MA_low_lim'].values)
                        ind_pow_ax[x][y].set_ylim(-30, 5)
                        ind_pow_ax[x][y].tick_params(axis='y', labelsize=8)
                        ind_pow_ax[x][y].tick_params(axis='x', labelsize=8, rotation=45)   
                        ind_pow_ax[x][y].minorticks_on()
                        ind_pow_ax[x][y].tick_params(which='minor', width=0.5)  
                        #ind_pow_ax[x][y].legend(fontsize=4, edgecolor='k', loc='upper center', ncol=8)
                        ind_pow_fig.supylabel("Power (dBm)", family="Times New Roman", fontsize=12)
                        ind_pow_fig.suptitle('Power at peak', family="Times New Roman", fontsize=12)
                        ind_pow_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                        
                        # sing chan 
                        if i == args.sing_chan:
                                
                            sing_chan_ax[0].plot(sampled_df.index.values,  sampled_df['mu'].values, color=colorstyle[i], linewidth=0.6, label="Waveform $\mu$")
                            sing_chan_ax[0].plot(sampled_df.index.values,  sampled_df['mu_MA'].values)
                            sing_chan_ax[0].plot(sampled_df.index.values,  sampled_df['mu_MA_up_lim'].values)
                            sing_chan_ax[0].plot(sampled_df.index.values,  sampled_df['mu_MA_low_lim'].values)
                            sing_chan_ax[0].tick_params(axis='y', labelsize=8)
                            sing_chan_ax[0].tick_params(axis='x', labelsize=8, rotation=45)   
                            sing_chan_ax[0].minorticks_on()
                            sing_chan_ax[0].tick_params(which='minor', width=0.5)  
                            sing_chan_ax[0].legend()
                            sing_chan_ax[0].set_ylabel("Wavelength [nm]")
                            

                            sing_chan_ax[1].plot(sampled_df.index.values,  sampled_df['sigma'].values, color=colorstyle[i], linewidth=0.6, label="Waveform $\sigma$")
                            sing_chan_ax[1].plot(sampled_df.index.values,  sampled_df['sig_MA'].values)
                            sing_chan_ax[1].plot(sampled_df.index.values,  sampled_df['sig_MA_up_lim'].values)
                            sing_chan_ax[1].plot(sampled_df.index.values,  sampled_df['sig_MA_low_lim'].values)
                            sing_chan_ax[1].tick_params(axis='y', labelsize=8)
                            sing_chan_ax[1].tick_params(axis='x', labelsize=8, rotation=45)   
                            sing_chan_ax[1].minorticks_on()
                            sing_chan_ax[1].tick_params(which='minor', width=0.5) 
                            sing_chan_ax[1].legend()
                            sing_chan_ax[1].set_ylabel("Standard Deviations [$\sigma$]")

                            sing_chan_ax[2].plot(sampled_df.index.values,  sampled_df['peak_wavelength'].values, color=colorstyle[i], linewidth=0.6, label="Wavelength at Peak")
                            sing_chan_ax[2].plot(sampled_df.index.values,  sampled_df['wave_MA'].values)
                            sing_chan_ax[2].plot(sampled_df.index.values,  sampled_df['wave_MA_up_lim'].values)
                            sing_chan_ax[2].plot(sampled_df.index.values,  sampled_df['wave_MA_low_lim'].values)
                            sing_chan_ax[2].tick_params(axis='y', labelsize=8)
                            #sing_chan_ax[2].tick_params(axis='x', labelsize=8, rotation=45)   
                            sing_chan_ax[2].minorticks_on()
                            sing_chan_ax[2].tick_params(which='minor', width=0.5)
                            sing_chan_ax[2].legend() 
                            sing_chan_ax[2].set_ylabel("Wavelength [nm]")
                            
                            sing_chan_ax[3].plot(sampled_df.index.values,  sampled_df['peak_power'].values, color=colorstyle[i], linewidth=0.6, label="Power at Peak")
                            sing_chan_ax[3].plot(sampled_df.index.values,  sampled_df['pow_MA'].values)
                            sing_chan_ax[3].plot(sampled_df.index.values,  sampled_df['pow_MA_up_lim'].values)
                            sing_chan_ax[3].plot(sampled_df.index.values,  sampled_df['pow_MA_low_lim'].values)
                            sing_chan_ax[3].tick_params(axis='y', labelsize=8)
                            sing_chan_ax[3].tick_params(axis='x', labelsize=8, rotation=45)   
                            sing_chan_ax[3].minorticks_on()
                            sing_chan_ax[3].tick_params(which='minor', width=0.5)
                            sing_chan_ax[3].legend() 
                            sing_chan_ax[3].set_ylabel("Power [dBm]")
                            sing_chan_ax[3].set_xlabel("Date")

                            #sing_chan_fig.supylabel("Power (dBm)", family="Times New Roman", fontsize=12)
                            sing_chan_fig.suptitle('Channel %d Statistics'%i, family="Times New Roman", fontsize=12)
                            sing_chan_fig.subplots_adjust(left=0.1, bottom=0.1, right=0.99, top=0.99, wspace=0.7, hspace=0.12)
                            
                        mu_out = sampled_df['mu_outside'].any()
                        sig_out = sampled_df['sig_outside'].any()
                        wave_out = sampled_df['wave_outside'].any()
                        pow_out = sampled_df['pow_outside'].any()

                        reports.append(["mu alert: "+str(mu_out),"sigma alert: "+str(sig_out),"wave alert: "+str(wave_out),"power alert: "+str(pow_out)])
                        #progress
                        sys.stdout.write("\rChannel number: %d" % i)
                        sys.stdout.flush()
                    
                    ts1 = pd.to_datetime(sampled_df.index.values[0]) 
                    str_of_first_day = ts1.strftime('%Y-%m-%d')
                    ts = pd.to_datetime(sampled_df.index.values[-1]) 
                    str_of_last_day = ts.strftime('%Y-%m-%d')
                    mu_fig.savefig("pythonic_waveform_mu_all_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         
                    ind_mu_fig.savefig("pythonic_waveform_mu_ind_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         
                    sig_fig.savefig("pythonic_waveform_sigma_all_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         
                    ind_sig_fig.savefig("pythonic_waveform_sigma_ind_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         
                    peak_fig.savefig("pythonic_wavelength_at_peak_all_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         
                    ind_peak_fig.savefig("pythonic_wavelength_at_peak_ind_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         
                    pow_fig.savefig("pythonic_power_at_peak_all_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         # save figure
                    ind_pow_fig.savefig("pythonic_power_at_peak_ind_channels_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         # save figure
                    sing_chan_fig.savefig("pythonic_sing_chan_"+str_of_last_day+".png", dpi=fig_dpi, bbox_inches='tight')         # save figure
                    mu_fig.clf()         
                    ind_mu_fig.clf()         
                    sig_fig.clf()         
                    ind_sig_fig.clf()         
                    peak_fig.clf()         
                    ind_peak_fig.clf()         
                    pow_fig.clf()
                    ind_pow_fig.clf()
                    sing_chan_fig.clf()
                    
                    # If we got here, write the report   
                    with open("status_report_"+str_of_last_day+".txt","w") as rep:
                        
                        rep.writelines(['Report for '+str_of_first_day+' to '+str_of_last_day,'\n'])
                        for i in range(64):  
                            rep.writelines(['\n','Channel '+str(i)+" report: ",'\n'])  
                            for alert in reports[i]:
                                rep.writelines([alert,"\n"])
                                if alert.split(' ')[-1] == "True":
                                    print("alert!")
                    print('\nWrote report for '+str_of_last_day)

            time.sleep(args.rr)
    else:
        print("RERUN PROGRAM, FAILED TO START, SELECT PROPER DAY OF WEEK, DEFAULT IS MONDAY")
    
if __name__ == '__main__':
    main()