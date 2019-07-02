#!/usr/bin/python

import sys

def get_numberstr(pos, String):
	numstr=""
	while True:
		if string[pos] == 'L':
			return numstr
		numstr += string[pos]
		pos+=1

def main():
	Fw = open("./saveydns.logs", mode='r')
	String = Fw.readline()
	pos = String.find("rx_pkts")
	if pos != -1:
		pos2 = String.find("rx_pkts", pos+1)
		pos2+=10
		pos+=10

		num = ""
		num2 = ""
			
		num = int(get_numberstr(pos, String))
		num2 = int(get_numberstr(pos2, String))
		print num + num2
	else:
		print 0
	Fw.close()

if __name__=="__main__":
	sys.exit(main())
