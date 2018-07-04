from Blocky.Pin import *
from machine import Pin , ADC
from Blocky.Timer import AddTask
class Servo:
	def __init__ (self , port , min=400 , max = 2600)
		p = getPin(port)
		if p[2] == None or p[1] == None : return 
		self.pwm = PWM(Pin(p[1]),freq = 50)
		self.adc = ADC(Pin(p[2]))
		self.adc.atten(ADC.ATTN_11DB)
		self.min = min
		self.max = max
		
	def angle(self,value = None ):
		if value == None :
			return self.adc.read()
		else :
			self.pwm.init()
			self.pwm.duty ( (value - 0) * (120 - 10) // (180 - 0) + 10 )
			AddTask(name='servo'+str(p[2]) , mode='once',time=1000,function = self.pwm.deinit)
			