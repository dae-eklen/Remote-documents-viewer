import socket
from os import sep, path
import os
import md5
import sys
import time
import subprocess
import re

#HOST = "192.168.0.101"
HOST = "127.0.0.1"
PORT = 5000

BUF = 8*1024
DEFAULT_DIR = os.path.abspath("home")

class Client:
	def __init__(self, HOST, PORT):		
		self.socket = socket.socket()
		self.dir = DEFAULT_DIR
		try:
			self.socket.connect((HOST, PORT))
		except:
			print "\tserver is down"
			self.socket.close()
			sys.exit(1)
	
	def work(self):
		while True:
			message = raw_input("type command: ").strip()	
			if message:
				try:
					self.socket.send(message)
				except:
					print "\tserver is down"
					self.socket.close()
					break
				
				if message[:4] == "get ":
					self.accept_file(message[4:])
					continue	

				if message == "root" or message[:5] == "list ":
					self.show_dir()
					continue						
			
			try:
				received = self.socket.recv(BUF)
				print "- I received from server: ", received
				if (received == "down"):
					self.socket.close()
					print "\tshutting down"
					break
			except socket.error:
				print "\tserver is down"
				self.socket.close()
				break
	
	
	def get_file(self, path):
		path = path.replace("/", "\\")
		self.socket.send('get ' + path)
		print "sent", 'get ' + path
		self.accept_file(path)
		
		self.socket.send('stop')
		received = self.socket.recv(BUF)
		if (received == "down"):
			self.socket.close()
			print "\tshutting down"
		
	
	def show_dir(self):
		received = self.socket.recv(BUF)
		if received == "error: no directory or file found":
			print "\t" + received
			return
		escaped = received.replace("\\\\", "\\")
		directory_list = escaped[2:-2].split("', '")
		for el in directory_list:
			print "\t" + el
				
	def accept_file(self, file):
		list = file.split("\\")
		self.fName = ''
		for item in list:
			self.fName = item
		
		# receive size
		size = self.socket.recv(BUF)
		if size == "error: wrong file format" or size == "error: no file found":
			print "\t" + size
			return
		print "\t" + self.print_size_speed(size, 'size')
		self.socket.send("checksum")
		
		#receive checksum md5
		sentChecksum = self.socket.recv(BUF)
		if sentChecksum == "error: wrong format":
			print "\terror: wrong format"
			return
		print "\tsent checksum:     ",sentChecksum
		self.socket.send("send")
					
		f = open(self.dir + sep + self.fName, "wb")
		self.socket.settimeout(1.0)
		timeLast = time.time()
		has = 0.0
		while True:
			try:
				timeNow = time.time()
				received = self.socket.recv(BUF)
				has += len(received)
				f.write(received)
				
				timePrint = time.time() - 100	
				timeDelta = (timeNow - timeLast)
				timeLast = time.time()
				try:
					#print "{} {} {}".format(time.time(), timePrint, time.time() - timePrint)
					if (timeDelta != 0):
						speed = self.print_size_speed(len(received)/timeDelta, 'speed')
						percent = round((has/float(size))*100, 2)
						print "\r\tspeed: " + speed + "\tprogress: " + repr(percent) + "%",
						timePrint = time.time()
					else:
						pass
				except Exception,e:
					print(e)
					
			except Exception,e:
				#print(e)
				f.close()
				self.socket.settimeout(None)
				break
		
		percent = round((has/float(size))*100, 2)
		print "\r\tprogress: " + repr(percent) + "%                                 ",
		
		if sentChecksum != "too large file to compute checksum":
			f = open(self.dir + sep + self.fName, "rb")
			fileContent = f.read()
			f.close()
			
			receivedChecksum = md5.new(fileContent).digest()
			print "\n\treceived checksum: ",receivedChecksum
			if sentChecksum == receivedChecksum:
				print "\tchecksums are equal"
			else:
				print "\tchecksums are not equal"
		
		self.display(self.dir + sep + self.fName)
	
	def display(self, file_path):
		list = file_path.split(".")
		ends_with = ''
		for item in list:
			ends_with = item
		"""
		if (path.getsize(file_path) < 1048576) and (ends_with == 'xml' or ends_with == 'txt'):
			f = open(file_path, "rb")
			print "\tcontent of {} file:".format(file_path)
			while True:
				data = f.read(BUF) 
				if not data:
					break
				print data
			f.close()
		"""
		
		answer = raw_input("\ndo you want to open received file ? (y/n) ").strip()	
		while True:
			if answer:
				if answer == 'y' or answer == 'Y':
					cmd = file_path
					s = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
					s.communicate()[0]
				break
	
	def print_size_speed(self, bytes, mode):
		bytes = float(int(bytes))
		if bytes >= 1048576:
			megabytes = bytes / 1048576
			val = '%.2f Mb' % megabytes
		elif bytes >= 1024:
			kilobytes = bytes / 1024
			val = '%.2f Kb' % kilobytes
		else:
			val = '%.2f b' % bytes
			
		if mode == 'size':
			res =  'file has ' + val
		elif mode == 'speed':
			res = val + '/s'
			
		return res

def set_dir():
	global DEFAULT_DIR
	message = "your current home directory is " + DEFAULT_DIR + \
		";\nenter new path or press 'y' to continue: "
	dir = raw_input(message).strip()	
	if dir != 'y' and dir != 'Y':
		DEFAULT_DIR = os.path.abspath(dir)
		if not os.path.exists(dir):
			try: 
				os.makedirs(dir)
				print "\t" + dir + " was created..."
			except:
				print "\tcannot create directory " + DEFAULT_DIR
		else:
			print "\tdirectory found"
	else:
		if not os.path.exists(DEFAULT_DIR):
			try: 
				os.makedirs(DEFAULT_DIR)
			except:
				print "\tcannot create directory " + DEFAULT_DIR
	#print "dir is ", dir
	#print "def dir is ", DEFAULT_DIR

def connection():			
	global HOST, PORT
	message = "enter 'E' to establish long-time connection with server;\
		\nor enter get command to retrieve a single file:\n"
	protocol = ''
	while True:		
		command = raw_input(message).strip()
		if command == 'e' or command == 'E':
			c = Client(HOST, PORT)
			c.work()
			break
		else:	
			patt = """([a-zA-Z]*)://([a-zA-Z0-9.]*):([0-9]*)/([a-zA-Z0-9./]*)"""
			# if port is optional:
			#patt = """([a-zA-Z]*)://([a-zA-Z0-9.]*)(:([0-9]*)|)/([a-zA-Z0-9./]*)"""
			matchList = re.findall(patt, command)
			if matchList == []:
				print "\twrong command"
				continue
			for i in matchList: 
				protocol, host, port, path = i 
			break
			
	if protocol == "tcp":
		c = Client(host, int(port))
		c.get_file(path)
	elif command != 'e' and command != 'E': 
		print "\twrong protocol or the protocol is not supported"
		
		
def main():
	set_dir()
	connection()	
				
	#c = Client(HOST, PORT)
	#c.work()
			
if __name__ == "__main__":
	main()
