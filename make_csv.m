sample_rate = 250 %Hz
amplitude   = 10 %mm
sin_freq    = 1 % Hz 
time = linspace(0,1,sample_rate)
positions = sin(2*pi*sin_freq*time)


plot(time, positions)
csvwrite("csv_export.csv",[positions', time'])