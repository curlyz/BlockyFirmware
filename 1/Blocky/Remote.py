from Blocky.Pin import getPin
from machine import Pin
from time import ticks_us
pin = Pin(14 , Pin.IN , Pin.PULL_UP)
flipper = 0
last = 0
def handler (state):
  global flipper
  global last 
  global c
  last = state.value()
  if last != flipper:
    c+=1
    flipper = last
    
def get():
  global c
  print(c)
  c = 0
  
pin.irq(trigger = Pin.IRQ_FALLING|Pin.IRQ_RISING , handler = handler)
