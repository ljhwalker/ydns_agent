#!/usr/bin/python

def get_numberstr(pos, string):
	numstr=""
	while True:
		if string[pos] == 'L':
			return numstr
		numstr += string[pos]
		pos+=1

fw = open("./saveydns.logs", mode='r')
string = fw.readline()
pos = string.find("rx_pkts")
if pos != -1:
	pos2 = string.find("rx_pkts", pos+1)
	pos2+=10
	pos+=10

	num = ""
	num2 = ""
		
	num = int(get_numberstr(pos, string))
	num2 = int(get_numberstr(pos2, string))
	print num + num2
else:
	print 0

fw.close()
