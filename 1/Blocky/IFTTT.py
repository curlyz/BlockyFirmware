
import urequests
import socket , gc
from time import sleep_ms
try:
    import ussl as ssl
except:
    import ssl
	
class IFTTT:
	def __init__ (self,key):
		self.key = key 
		self.topic = ''
		self.thread = None
	def trigger(self,topic,data='hi'):
		gc.collect()
		sock = urequests.get('https://maker.ifttt.com/trigger/' + self.topic + '/with/key/'+self.key)
		sock.close()
		gc.collect()
		

