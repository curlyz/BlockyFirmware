from machine import ADC , Pin 
from Blocky.Pin import getPin
class Light :
	def __init__ (self , port , sensitive = 4):
		pin = getPin(port)
		if (pin[2] == None):
			from machine import reset
			reset()
		
		self.adc = ADC(Pin(pin[2]))
		if (sensitive == 1): self.adc.atten(ADC.ATTN_0DB)
		elif (sensitive == 2): self.adc.atten(ADC.ATTN_2_5DB)
		elif (sensitive == 3): self.adc.atten(ADC.ATTN_6DB)
		elif (sensitive == 4): self.adc.atten(ADC.ATTN_11DB)
	def read(self):
		return self.adc.read()
		

