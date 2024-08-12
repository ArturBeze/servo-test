#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 27 13:42:46 2024

@author: artur
"""

import enum
import math
import time
import argparse
from threading import Thread
from PyQt5 import QtWidgets, uic
from PyQt5.QtSerialPort import QSerialPortInfo
from pyfirmata import Arduino, SERVO

class ServoStatus(enum.Enum):
	manual = 0
	neutral = 1
	auto = 2

class ServoController():
	def __init__(self, pin, maxAngle):
		self.pin = pin
		self.maxAngle = maxAngle
		self.stopped = False
		self.status = ServoStatus.neutral
		
	def start(self):
		#port = 'COM3'# Windows
		#port = '/dev/ttyACM3' # Linux
		#port = '/dev/tty.usbmodem11401'# Mac
		
		ports = QSerialPortInfo().availablePorts()
		for port in ports:
			if "tty.usbmodem" in port.portName() and "Arduino" in port.manufacturer():
				self.board = Arduino(f"/dev/{port.portName()}")
				self.board.digital[self.pin].mode = SERVO
				break
		else:
			raise ValueError("Arduino device is not connected")
			
		self.setServoNeutral()
		
		thread = Thread(target=self.update, args=())
		thread.daemon = True
		thread.start()
		
	def update(self):
		increment = True
		
		while True:
			if self.stopped:
				return
			
			time.sleep(.1)
			
			if self.status == ServoStatus.auto:
				if increment:
					self.angle += 1
				else:
					self.angle -= 1
				
				time.sleep(.001)
				
				if self.angle >= 180: 
					increment = False
				elif self.angle <= 0:
					increment = True
					
				self.setServoPosition(self.angle)
				
				print("Servo is auto")
				
	def stop(self):
		self.board.exit()
		self.stopped = True
		
	def setServoNeutral(self):
		self.angle = math.floor(self.maxAngle/2)
		self.setServoPosition(self.angle)
	
	def setServoPosition(self, val):
		self.board.digital[self.pin].write(val)
		
	def getServoStatus(self):
		return self.status

def main():
	def dialControl(val):
		if servo.getServoStatus() == ServoStatus.manual:
			ui.angleL.setText(f"Angle: {val}")
			servo.setServoPosition(val)
		print(f"dialControl {val}")

	def neutralControl():
		servo.status = ServoStatus.neutral
		ui.angleD.setValue(math.floor(args.angle/2))
		ui.angleL.setText(f"Angle: {math.floor(args.angle/2)}")
		servo.setServoNeutral()
		print(f"neutralControl")

	def manualControl():
		servo.status = ServoStatus.manual
		ui.angleL.setText(f"Angle: {ui.angleD.value()}")
		servo.setServoPosition(ui.angleD.value())
		print(f"manControl")

	def autoControl():
		servo.status = ServoStatus.auto
		ui.angleL.setText(f"Angle: {ui.angleD.value()}")
		servo.setServoPosition(ui.angleD.value())
		print(f"autoControl")

	parser = argparse.ArgumentParser(description="Servo tester")
	parser.add_argument("--angle", type=int, help="servo motor maximum angle", default=180)
	parser.add_argument("--pin", type=int, help="servo motor PWM pin", default=9)
	args = parser.parse_args()
	
	print("Test servo motor with {0} angle and connected to {1} PWM pin".format(args.angle, args.pin))

	servo = ServoController(args.pin, args.angle)
	servo.start()

	app = QtWidgets.QApplication([])

	ui = uic.loadUi("testerGUI.ui")
	ui.setWindowTitle("TesterGUI")

	ui.neutralRB.pressed.connect(neutralControl)
	ui.manualRB.pressed.connect(manualControl)
	ui.autoRB.pressed.connect(autoControl)
	ui.angleD.valueChanged.connect(dialControl)

	ui.show()
	app.exec()
	
	servo.setServoNeutral()
	servo.stop()

if __name__ == "__main__":
	main()