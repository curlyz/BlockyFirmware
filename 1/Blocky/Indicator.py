from machine import Pin
from neopixel import NeoPixel
from Blocky.Pin import getPin
from Blocky.Timer import *
from time import sleep_ms
class Indicator :
	def __init__ (self):
		self.animation = ''
		self.color = (0,0,0) # color that user set 
		self.fcolor = [0,0,0] # color that the handler use
		self.rgb = NeoPixel(Pin(5) , 1 , timing = True )
	def animate (self , type = 'None', color = (0,100,100), speed =10):
		self.rgb[0] = color
		self.rgb.write()
		sleep_ms(1)
		self.rgb[0] = (0,0,0)
		self.rgb.write()
		
		# Timer has been penalty because of its unstable behaviour 
		# DEPRECATED
		"""
		print('set to ' , color , type );self.rgb[0] = (0,0,0)
		if type == 'heartbeat':
			self.animation = type
			self.color = color 
			def _handler (self):
				r,g,b = self.rgb[0]
				if (r,g,b) == (0,0,0):	self.fcolor = self.color
				if (r,g,b) == self.fcolor:self.fcolor = (0,0,0)
				d,e,f = self.fcolor
				if (r<d): r = r + 1
				if (r>d): r = r - 1 if r > 1 else 0
				if (g<e): g = g + 1
				if (g>e): g = g - 1 if g > 1 else 0
				if (b<f): b = b + 1
				if (b>f): b = b - 1 if b > 1 else 0
				self.rgb[0] =  (r,g,b)
				self.rgb.write()
			AddTask(name = 'sys_led' , function = _handler , mode = 'repeat',time = speed,arg = (self))
		elif type == 'pulse':
			
			self.animation = type
			self.color = (color[0]//5*5,color[1]//5*5,color[2]//5*5) 
			self.fcolor = (color[0]//5*5,color[1]//5*5,color[2]//5*5) 
			self.rgb[0]  = (0,0,0)
			def _handler (self):
				global r,g,b
				r,g,b = self.rgb[0]
				if (r,g,b) == self.color:self.fcolor = (0,0,0)
				d,e,f = self.fcolor
				if (r<d): r = r + 5
				if (r>d): r = r - 5 if r > 5 else 0
				if (g<e): g = g + 5
				if (g>e): g = g - 5 if g > 5 else 0
				if (b<f): b = b + 5
				if (b>f): b = b - 5 if b >5 else 0
				self.rgb[0] =  (r,g,b)
				self.rgb.write()
				if self.rgb[0] == (0,0,0):
					DeleteTask('sys_led')
					
			AddTask(name = 'sys_led' , function = _handler , mode = 'repeat',time = speed,arg = (self))
		else :
			DeleteTask('sys_led')
			self.rgb[0] = (0,0,0) ; self.rgb.write()
		"""
indicator = Indicator()

	





