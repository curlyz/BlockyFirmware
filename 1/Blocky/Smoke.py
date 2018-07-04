from machine import ADC , Pin 
from Blocky.Pin import getPin

class Smoke :
	def __init__ (self , port , sensitive = 4):
		p = getPin(port)
		if (getPin(port)[2] == None):
			return 
		self.adc = ADC(Pin(p[2]))
		if (sensitive == 1) :self.adc.atten(ADC.ATTN_0DB)
		elif (sensitive == 2): self.adc.atten(ADC.ATTN_2_5DB)
		elif (sensitive == 3): self.adc.atten(ADC.ATTN_6DB)
		elif (sensitive == 4): self.adc.atten(ADC.ATTN_11DB)
	def read(self):
		return self.adc.read()
		


