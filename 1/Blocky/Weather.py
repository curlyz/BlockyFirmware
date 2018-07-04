# AN2001 
from machine import Pin
from dht import *
from Blocky.Pin import getPin
from Blocky.Timer import runtime
import Blocky.uasyncio as asyncio

class Weather:
	def __init__ (self , port,module='DHT11'):
		pin = getPin(port)
		if (pin[0] == None):
			from machine import reset
			reset()
		if module == 'DHT11': self.weather = DHT11(Pin(pin[0]))
		elif module == 'DHT22': self.weather = DHT22(Pin(pin[0]))
		elif module == 'DHTBase': self.weather = DHTBase(Pin(pin[0]))
		else :
			raise NameError
		self.last_poll = runtime()
		self.cb_humidity = None
		self.cb_temperature = None
		self._handler = False
	def temperature (self):
		if runtime() - self.last_poll > 2000:
			self.last_poll = runtime()
			try :
				self.weather.measure()
			except Exception:
				pass
		return self.weather.temperature()
	def humidity(self):
		if runtime() - self.last_poll > 2000:
			self.last_poll = runtime()
			try :
				self.weather.measure()
			except Exception:
				pass
		return self.weather.humidity()
	
	def event(self,type,function):
		if type == 'temperature':
			self.cb_temperature = function 
		if type == 'humidity':
			self.cb_humidity = function
		if not self._handler:
			try :
				loop = asyncio.get_event_loop()
				print(str(self.handler()))
				if not str(self.handler()).split("'")[1] in loop.tasks:
					self._handler = True 
					loop.call_soon(self.handler())
					
			except Exception:
				pass
		
	async def handler(self):
		
		while True :
			temp = self.weather.temperature()
			humd = self.weather.humidity()
			
			await asyncio.sleep_ms(2500)
			try :
				self.weather.measure()
			except Exception:
				pass
			if self.weather.temperature() != temp and self.cb_temperature:
				try :
					self.cb_temperature(self.weather.temperature())
				except Exception:
					pass
			if self.weather.humidity() != humd and self.cb_humidity:
				try :
					self.cb_humidity(self.weather.humidity())
				except Exception:
					pass
				
			
		



