import socket
import time
import datetime
from os import path, sep, stat
import os
import sys
import md5
import thread
from threading import Lock

HOST = "127.0.0.1"
PORT = 5000
IP = socket.gethostbyname(socket.gethostname())
print "server's ip and port:", IP, " ", PORT
IN_QUEUE = 5

BUF = 8*1024 # 8*1 Kb

# default root directory:
#DIR = "."
#DIR = os.path.abspath(".\docs")
DIR = ".\docs"

class DirWalker(object):
	def walk(self, DIR, dir_content):
		# walks a directory, and executes a callback on each file
		#DIR = os.path.abspath(DIR)
		for file in os.listdir(DIR):
			nfile = os.path.join(DIR, file)
			if os.path.isdir(nfile):
				self.walk(nfile, dir_content)
			else:				
				print (nfile)
				dir_content.append(nfile)

class Server:
	def __init__(self, HOST, PORT):
		self.socket = socket.socket()
		self.socket.bind((HOST, PORT))
		self.socket.listen(IN_QUEUE)
		print "started"
		
	def work(self):	
		#self.socket.settimeout(1.0)
		while True:
			#try:
			clientSocket, remoteAddress = self.socket.accept()
			thread.start_new_thread(self.talk_to_client,(clientSocket, remoteAddress))
			#except:
				#continue

	def talk_to_client(self, clientSocket, remoteAddress):
		print "got client: ", remoteAddress
		while True:
			try:
				clientSocket.settimeout(None)
				received = clientSocket.recv(BUF).strip()
				print "- I received from client {}: {}".format(remoteAddress, received)	

				if received == "checksum":
					if path.getsize(self.file) < 1024*1024*100: #if < 100 Mb
						try:
							f = open(self.file, "rb")
							fileContent = f.read()
							f.close()
							checksum = md5.new(fileContent).digest()
							clientSocket.send(checksum)
							print "\tchecksum is: ",checksum
						except:
							print "\terror: wrong format"					
							clientSocket.send("error: wrong format")
					else:
						print "\ttoo large file to compute checksum"					
						clientSocket.send("too large file to compute checksum")
					
				elif received == "send":
					lock = Lock()
					pos = 0
					while True:
						with lock:
							#print "lock enter"
							f = open(self.file, "rb")
							f.seek(pos)
							data = f.read(BUF) 
							if not data:
								break
							pos += len(data)
							try:
								clientSocket.send(data)
							except:
								print "can't send"
								break
							f.close()
							#print "lock exit"
						
				elif received == "stop":
					clientSocket.send('down')
					clientSocket.close()
					print "client {} disconnected".format(remoteAddress)
					return
						
				elif received == "days till ny":
					print "\t" + time.strftime("%A, %d %b %Y")
					today = datetime.date.fromtimestamp(time.time())
					ny = datetime.date(today.year, 12, 31)
					daystony = abs(ny-today)
					d = str(daystony.days)
					clientSocket.send(d)
						
				elif received == "root":
					dir_content = []
					DirWalker().walk(DIR, dir_content)
					clientSocket.send(str(dir_content))
					
				elif received[:5] == "list ":
					file = received[5:]
					try:
						if os.path.isdir(file):
							dir_content = []
							DirWalker().walk(file, dir_content)
							clientSocket.send(str(dir_content))
						else:			
							toSend = []
							list = file.split("\\")
							fName = ''
							for item in list:
								fName = item
							print fName
							toSend.append("file name:         " + fName)
							creationTime = time.ctime(os.stat(file)[8])
							print creationTime
							toSend.append("creation time:     " + creationTime)
							modTime = time.ctime(os.stat(file)[9])
							print modTime
							toSend.append("modification time: " + modTime)
							size = self.print_size_speed(os.stat(file)[6], 'size')
							print size
							toSend.append("size:              " + size)
							clientSocket.send(str(toSend))
					except:
						print "\terror: no directory or file found"				
						clientSocket.send("error: no directory or file found")

				elif received[:4] == "get ":
					self.file = received[4:]
					try:
						if os.path.isdir(self.file):
							print "\terror: wrong file format"					
							clientSocket.send("error: wrong file format")
						else:
							clientSocket.send(str(path.getsize(self.file)))
							print "\tsent file size - ",path.getsize(self.file)
					except:
						print "\terror: no file found"				
						clientSocket.send("error: no file found")
						
				else:
					clientSocket.send("Can you elaborate on that?")
	
			except:
				continue
		
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
			
			
def main():
	print "your current root directory is " + os.path.abspath(DIR) 	
	
	s = Server(HOST, PORT)
	s.work()
			
if __name__ == "__main__":
	main()
