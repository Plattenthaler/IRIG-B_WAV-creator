# Sebastian Melzer 06.08.2019

import wave, struct, math
import numpy
import matplotlib
import matplotlib.pyplot as plt
from scipy.io import wavfile

#**********************************************editable information**********************************************************
sampleRate = 44100 # hertz
duration = 1     # playback time of the wav-file seconds
frequency = 1000.0 # Modulation frequency of the IRIG-code in hertz
ratio = 3.3/1	   # between high and low amplitude (standart 6/1 to 3/1)

# specify here the automatic incremented date in the file
# Importand: Seconds of a day are not updated!!! (not implemented yet)
year = 2019
days=262
hours=16
minutes=42
seconds=0

#**********************************************/end editable information**********************************************************

# Initial points arn't interresting. Just for debuging. I read the image and putted the bits in this two arrays 
#(acording to the picture: Time 173 Days, 21 Hours, 18 Minutes, 42 Seconds, 03 Year (2003))
# Spource: 	http://manuals.spectracom.com/NC/Content/NC_and_SS/Com/Topics/APPENDIX/IRIGb.htm

p=2
points_part1=[p,0,1,0,0,0,0,0,1,p,0,0,0,1,0,1,0,0,0,p,1,0,0,0,0,0,1,0,0,p,1,1,0,0,0,1,1,1,0,p,1,0,0,0,0,0,0,0,0,p]
points_part2=[1,1,0,0,0,0,0,0,0,p,0,0,0,0,0,0,0,0,0,p,0,0,0,0,0,0,0,0,0,p,0,1,0,0,1,1,0,1,1,p,1,0,1,0,1,0,0,1,0,p]

def dec_to_bin(integer, digits=0):
	#from: https://www.geeksforgeeks.org/python-decimal-to-binary-list-conversion/
	# using format() + list comprehension 
	# decimal to binary number conversion  
	integer = int(integer)
	res = [int(i) for i in list('{0:0b}'.format(integer))] 
	if len(res) < digits:
		for difference in range(0,digits-len(res)):
			res = [0] + res
	return res
	

def setSeconds(sec):
	# print (str(sec-1)+ " " + str(points_part1))
	#first seconds 0-9
	sec = int(sec)%60
	for index, i in enumerate(list(reversed(dec_to_bin(sec%10,4)))):
		points_part1[index+1]=i
	#second 00-50
	for index, i in enumerate(list(reversed(dec_to_bin(sec/10,3)))):
		points_part1[index+6]=i
		
def setMinutes(minutes):
	#first minutes 0-9
	minutes = int(minutes)%60
	for index, i in enumerate(list(reversed(dec_to_bin(minutes%10,4)))):
		points_part1[index+10]=i
	#minutes 00-50
	for index, i in enumerate(list(reversed(dec_to_bin(minutes/10,3)))):
		points_part1[index+15]=i

def setHours(hours):
	#first hours 0-9
	hours = int(hours)%60
	for index, i in enumerate(list(reversed(dec_to_bin(hours%10,4)))):
		points_part1[index+20]=i
	#hours 00-50
	for index, i in enumerate(list(reversed(dec_to_bin(hours/10,3)))):
		points_part1[index+25]=i
		
def setSecOfDay(sec_of_day_k):
	# first set BCD coded time 
	setHours(sec_of_day_k/60/60)
	setMinutes(int(sec_of_day_k/60)%60)
	setSeconds(int(sec_of_day_k)%60)
	# set the second of day in the second of day output:
	sec_of_day_k
	offset=30
	for index, i in enumerate(list(reversed(dec_to_bin(sec_of_day_k,17)))):
		if index == 9:
			points_part2[index+offset]=p # for Position identifier
			offset+=1
			points_part2[index+offset]=i
		else:
			points_part2[index+offset]=i
			
def setDay(day_t):
	day_t = int(day_t)%366
	#example day 173
	#first 3
	for index, i in enumerate(list(reversed(dec_to_bin(day_t%10,4)))):
			points_part1[index+30]=i
	# now 7
	for index, i in enumerate(list(reversed(dec_to_bin(int(day_t/10)%10,4)))):
			points_part1[index+35]=i
	#now 1
	for index, i in enumerate(list(reversed(dec_to_bin(int(day_t/100)%10,2)))):
			points_part1[index+40]=i
		
def setYear(year_t):
	year_t = int(year_t)%100 # from 0 to 99
	#example 2019
	#first 9
	for index, i in enumerate(list(reversed(dec_to_bin(year_t%10,4)))):
			points_part2[index+0]=i	
	# now 7
	for index, i in enumerate(list(reversed(dec_to_bin(int(year_t/10)%10,4)))):
			points_part2[index+5]=i
			
def setTime(this_seconds_of_a_day, this_day, this_year):
	setSecOfDay(this_seconds_of_a_day)
	setDay(this_day)
	setYear(this_year)
	
def secondOfDayToText(sec_of_day_f):
	return "%02d:%02d:%02d" % (sec_of_day_f/60/60,int(sec_of_day_f/60)%60,int(sec_of_day_f)%60)

seconds_counter_of_a_day=seconds + minutes*60 + hours*60*60
seconds_counter_of_a_day+=-1 #because it will be incremented immediate 
bit_counter=0
millisec=0
h=32767.0 # => 2^15-1
l=h/ratio
amplituden_list=[	[h,h,l,l,l,l,l,l,l,l], #amplituden_list[0] = LOW, amplituden_list[1] = High, amplituden_list[p] = position Identifier
					[h,h,h,h,h,l,l,l,l,l],
					[h,h,h,h,h,h,h,h,l,l]]
output_arr= numpy.zeros((int(duration * sampleRate)), dtype=numpy.int16)
unmodulated_arr= numpy.zeros((int(duration * sampleRate)), dtype=numpy.int16)

for i in range(int(duration * sampleRate)):
	millisec=int(i*1000/sampleRate)
	if (i%int(sampleRate)==0):
		seconds_counter_of_a_day+=1
		setTime(seconds_counter_of_a_day, days, year)
	bit_counter=int(millisec/10)%100
	if(bit_counter<50):
		bit = points_part1[bit_counter]
	else:	
		bit = points_part2[bit_counter-50]
	amplitude=amplituden_list[bit][int(millisec)%10]
	output_arr[i] = int(amplitude*math.sin(frequency*2*math.pi*i/sampleRate))
	unmodulated_arr[i]=bit
	# if(i%int(sampleRate/1000)==0):
		# print("sample: %06d millisec: %04d bit_counter: %02d amplitude: %5d" % (i, millisec, bit_counter, amplitude))
	
wavfile.write("irgig_synthetic.wav", int(sampleRate), output_arr)

fig, ax = plt.subplots()
x_arr=numpy.arange(0,duration*100,100/sampleRate)
ax.plot(x_arr, output_arr/h)  # normed graph modulated signal
ax.plot(x_arr, unmodulated_arr)  # unmodulated signal

ax.set(xlabel='time (10 ms = 1 bit)', ylabel='amplitude (normed)',
       title='Output-wave')
ax.grid()
plt.show()
