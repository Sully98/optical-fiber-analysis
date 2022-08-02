import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import norm
from scipy.optimize import curve_fit
from scipy import asarray as ar,exp
from math import sqrt, log10
#-------------------------------------------------------------------------------------------------------------#
## get parameter function
def get_parameter(filename):                                            # calculate waveform parameters

    df = pd.read_table(filename, delim_whitespace=True, index_col=0, names=['Wavelength', 'OpticalPower']) 
    # print (df)

    x = df.index.to_list()                                          
    y = df['OpticalPower'].to_list()
    y_new = [10**(i/10 - 3) for i in y]

    mu = sum([a*b for a,b in zip(x,y_new)]) / sum(y_new)
    x0 = [i - mu for i in x]
    x0_2 = [i**2 for i in x0]
    sigma_2 = sum( [a*b for a,b in zip(x0_2,y_new)] ) / sum(y_new)
    sigma = sqrt(sigma_2)

    # print (mu,sigma)

    peak_wavelength = df['OpticalPower'].idxmax(axis=0)
    # print (peak_wavelength)

    peak_power = df['OpticalPower'].max()
    # print (peak_power)

    total_power = sum(y_new) * 0.015
    # print ('total power', total_power)

    total_dBm = 10 * log10(total_power * 1000)                              
    # print ('total dBm', total_dBm)
    return [mu, sigma, peak_wavelength, peak_power, total_power, total_dBm]                 

#-------------------------------------------------------------------------------------------------------------#
def get_date_time(filename):
    filename_list = filename.replace("waveform_data_channel", "").replace(".txt", "").split('_')
    # print (filename_list[1:])
    return filename_list[1:]

#-------------------------------------------------------------------------------------------------------------#
def main():
    for i in range(0,64):
        out_filename = 'Waveform_parameter_20220627\Channel%s_out_parameter.txt'%i                                                      # parameters file name
        with open(out_filename, 'w') as infile:
            infile.write('date time mu sigma peak_wavelength peak_power total_power total_dBm')      # first line of the parameters file
            infile.write('\n')
            for root, dirs, files in os.walk("Waveform_data_20220627"):                                      # search files in directory
                print(root)
                print(dirs)

                file_list = sorted(files,  key=lambda x: os.path.getmtime(os.path.join(os.path.join(root), x)))         # order file by creation time
                print(file_list)
                for file in file_list:
#                    if len(file) == 46:
#                        flen = int(file.split("_")[2][-1:])
#                    elif len(file) == 47:
#                        flen = int(file.split("_")[2][-2:])
#                    else:
#                        sys.exit('length of an file name is wrong, please check')
                    channel_ss = file.split("_")[2]
                    channel_nn = (channel_ss[-1:],channel_ss[-2:])[len(channel_ss) == 9]
                    chn = int(channel_nn)

                    if file.endswith(".txt") and chn == i:
                        print(file)
                        full_filename = os.path.join(root, file)
                        print(os.path.join(root, file))
                        par_list = get_parameter(full_filename)                                 # return back calculation parameters
                        print (par_list)

                        date_time_list = get_date_time(file)                                    # return back file date
                        print(date_time_list)

                        for item in date_time_list:                                                 # write waveform parameters into file
                            infile.write('%s '%item)
                        for listitem in par_list:                                                   # write file date into file
                            infile.write('%s ' % listitem)
                        infile.write('\n')

#-------------------------------------------------------------------------------------------------------------#
if __name__ == '__main__':
    main()