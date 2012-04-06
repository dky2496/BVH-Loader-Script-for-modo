# python


# BVHLoader script for modo is tri-licensed under MPL1.1/GPL2.0/LGPL2.1.
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.

# version 0.91 (2012/04/06)
# author: dky2496 ( http://twitter.com/#!/dky2496 )


import sys
import lx
import os

#from bvh import BVHReader
import bvh


# BVHReader
class BVHReader(bvh.BVHReader):
    
	def __init__(self, filename):
		bvh.BVHReader.__init__(self, filename)
		
		self.scaleFactor = 0.01			# scale multiplyer 
		self.swapXZ = False
		self.readJointOnly = False 		# skip read motion
		self.rotOrder = "flipBVH"
		self.createParentLocator = True
		self.fps = 30
		
		self.adaptFPS = False
		self.frameMode = "AdaptToBVH"
		
		self.useBVHrate = False
		self.rootPin = False
		self.rootPinLimit = 0
		self.applyZeroTransform = False
		
		self.currentTime = 0
		
		
	# ---------------------------------------------------
	def onHierarchy(self, root):
		
		fileRootItemID = None
		if self.createParentLocator:
			lx.eval("item.create locator")
			fileRootItemID = lx.eval("query sceneservice selection ? locator")
			lx.eval("item.name %s" % self.fileName)
		
		self.createSkeleton(root,fileRootItemID)
		self.root = root
		
		if self.readJointOnly == True:
			# exit
			sys.exit()
			
	# ---------------------------------------------------
	def onMotion(self, frames, dt):
		self.frames = frames
		self.dt = dt
		self.currentframe = 0
		
		if self.adaptFPS == True or self.frameMode == "AdaptToBVH":
			# calc from bvh file
			self.calcFps()

		self.fps = lx.eval("time.fpsCustom ?")
		
		lx.eval("time.range scene out:[%s f] [0] [0]" % self.frames)
		lx.eval("time.range current out:[%s f] [0] [0]" % self.frames)
		
		lx.eval("anim.autoKey off")
		
		lx.out("Total Frames: %s, FPS: %s, Deltatime: %s" % (self.frames,self.fps, self.dt))
		monitor.init(frames)
		
	# ---------------------------------------------------
	def onFrame(self, values):
		#called on each frame
		
		try:
			if self.frameMode == "AdaptToBVH" or self.frameMode == "UseSceneFrameRate":
				lx.eval("select.time [%s f] [0] [0]" % self.currentframe)
			else:
				lx.eval("select.time %s" % self.currentTime)

			#lx.out("Frame: %s, Time: %s" % (self.currentframe,self.currentTime))

			self.applyMotion(self.root, values)
			self.currentframe += 1
			self.currentTime += self.dt
			
			monitor.step()

		except: 
			lx.out("User Aborted")
			lx.eval("time.range current out:[%s f] [0] [0]" % self.currentframe)
			sys.exit()
		
	
	
	# calucrate fps ---------------------------------------------------
	def calcFps(self):
		#dt
		self.fps = round(1/self.dt)
		
		# set scene frame rate to bvh value
		lx.eval("time.fpsCustom %s" % self.fps)
	
	
	# apply Motion to the skelton ---------------------------------------------------
	def applyMotion(self, node, values):
		
# 		lx.out("Node : %s, Name: %s" % (node.id,node.name))
# 		lx.out("ISROOT" ,node._is_root)
		
		xfrmPos = lx.eval("query sceneservice item.xfrmPos ? %s" % node.id)
		xfrmRot = lx.eval("query sceneservice item.xfrmRot ? %s" % node.id)
		
# 		if xfrmPos is None:
# 			lx.eval("transform.add type:pos")
# 			xfrmPos = lx.eval("query sceneservice item.xfrmPos ? node.id")
# 		
# 		if xfrmRot is None:
# 			lx.eval("transform.add type:rot")
# 			xfrmRot = lx.eval("query sceneservice item.xfrmRot ? node.id")

		channelLength = len(node.channels)
		nodeVal = values[:channelLength]
		
		# root pin
		pin = 1
		if node._is_root == True and self.rootPin == True:
			pin = 0
		
		#lx.out("CHANNELS: %s, Length: %s" % (node.channels,len(node.channels)))
		
		if self.swapXZ == True:
			px = "pos.Z"
			pz = "pos.X"
		else:
			px = "pos.X"
			pz = "pos.Z"
		
		for ch,val in zip(node.channels, nodeVal):
			if ch == "Xposition":
				lx.eval("channel.key mode:add channel:{%s:%s} value:{%s}" % (xfrmPos,px,val * self.scaleFactor * pin))
			elif ch == "Yposition":
				lx.eval("channel.key mode:add channel:{%s:%s} value:{%s}" % (xfrmPos,"pos.Y",val * self.scaleFactor))
			elif ch == "Zposition":
				lx.eval("channel.key mode:add channel:{%s:%s} value:{%s}" % (xfrmPos,pz,val * self.scaleFactor * pin))
				
			elif ch == "Xrotation":
				lx.eval("channel.key mode:add channel:{%s:%s} value:{%s}" % (xfrmRot,"rot.X",val))
			elif ch == "Yrotation":
				lx.eval("channel.key mode:add channel:{%s:%s} value:{%s}" % (xfrmRot,"rot.Y",val))
			elif ch == "Zrotation":
				lx.eval("channel.key mode:add channel:{%s:%s} value:{%s}" % (xfrmRot,"rot.Z",val))
			
			
		
		# create children recursively
		values = values[channelLength:]
		for ch in node.children:
			values = self.applyMotion(ch,values)
		
		return values
		
	#create Skelton  -----------------------------------------------------------------
	def createSkeleton(self, node, parentID=None):
		# create Locator Item
		lx.eval("item.create locator")
		itemID = lx.eval("query sceneservice selection ? locator")
		node.id = itemID
		
		# add transform channels
		lx.eval("transform.add pos %s" % itemID)
		lx.eval("transform.add rot %s" % itemID)

		
		xfrmPos= lx.eval("query sceneservice item.xfrmPos ? %s" % itemID)
		xfrmRot = lx.eval("query sceneservice item.xfrmRot ? %s" % itemID)
		
		if xfrmPos is None:
			lx.eval("transform.add type:pos")
			xfrmPos = lx.eval("query sceneservice item.xfrmPos ? node.id")
		
		if xfrmRot is None:
			lx.eval("transform.add type:rot")
			xfrmRot = lx.eval("query sceneservice item.xfrmRot ? node.id")


		# set locator position`
		lx.eval("item.channel pos.X value:%s %s" % (node.offset[0] * self.scaleFactor,xfrmPos))
		lx.eval("item.channel pos.Y value:%s %s" % (node.offset[1] * self.scaleFactor,xfrmPos))
		lx.eval("item.channel pos.Z value:%s %s" % (node.offset[2] * self.scaleFactor,xfrmPos))
		
		# order
		order = self.rotationOrder(node.channels)
		if self.rotOrder == "BVH":
			ro = order
		elif self.rotOrder == "flipBVH":
			#flip order
			ro = order[::-1]
		else:
			ro = self.rotOrder
			
		lx.out("NAME: %s , OFFSET: %s , ORDER: %s" % (node.name,node.offset,ro))
		
		lx.eval("transform.channel order %s item:%s" % (ro,itemID))

		# set parent
		if parentID is not None:
			lx.eval("item.parent item:%s parent:%s inPlace:0" % (itemID,parentID))
			
		# set locator Attributes and shape 
		lx.eval("item.name %s" % node.name)
		
		if self.applyZeroTransform == True:
			lx.eval("transform.zero")

		lx.eval("item.channel locator$link custom")
		lx.eval("item.channel locator$lsShape rhombus")
		lx.eval("item.channel locator$drawShape custom")
		lx.eval("item.channel locator$isShape sphere")
		lx.eval("item.channel locator$isSolid false")
		lx.eval("item.channel locator$size %s" % (self.scaleFactor * 1))
		lx.eval("item.channel locator$isRadius %s" % (self.scaleFactor * 1))
		
			
		# create children recursively  
		for child in node.children:
			self.createSkeleton(child,itemID)
		

	# rotationOrder
	def rotationOrder(self, channels):
        #Determine rotation order string from the channel names.
		
		res = ""
		for c in channels:
			if c[-8:]=="rotation":
				res += c[0]

		# Complete the order string if it doesn't already contain
		# all three axes
		m = { "":"XYZ",
			"X":"XYZ", "Y":"YXZ", "Z":"ZXY",
				"XY":"XYZ", "XZ":"XZY",
				"YX":"YXZ", "YZ":"YZX",
				"ZX":"ZXY", "ZY":"ZYX" }
		if res in m:
			res = m[res]
			
				
		return res

		

		
	
# ============================================================
# main

lx.out( "Python Version: " ,sys.version)
lx.out( "Python path: " ,sys.path)

lx.trace(False)

# add uservalue
if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.scaleFactor"):
	lx.eval( "user.defNew BVHLoader.scaleFactor percent" )
	
if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.readJointOnly"):
	lx.eval("user.defNew BVHLoader.readJointOnly integer" )
	lx.eval("user.def BVHLoader.readJointOnly list on;off")

if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.rotOrder"):
	lx.eval("user.defNew BVHLoader.rotOrder integer" )
	lx.eval("user.def BVHLoader.rotOrder list BVH;flipBVH;XYZ;XZY;YXZ;YZX;ZXY;ZYX" )
	
# if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.adaptFPS"):
# 	lx.eval("user.defNew BVHLoader.adaptFPS integer" )
# 	lx.eval("user.def BVHLoader.adaptFPS list on;off")

if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.frameMode"):
	lx.eval("user.defNew BVHLoader.frameMode integer" )
	lx.eval("user.def BVHLoader.frameMode list AdaptToBVH;UseBVHTime;UseSceneFrameRate" )

	
if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.rootPin"):
	lx.eval("user.defNew BVHLoader.rootPin integer" )
	lx.eval("user.def BVHLoader.rootPin list on;off")
	
if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.rootPinLimit"):
	lx.eval("user.defNew BVHLoader.rootPinLimit float" )
	
if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.undoSuspend"):
	lx.eval("user.defNew BVHLoader.undoSuspend integer" )
	lx.eval("user.def BVHLoader.undoSuspend list on;off")

if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.createParentLocator"):
	lx.eval("user.defNew BVHLoader.createParentLocator integer" )
	lx.eval("user.def BVHLoader.createParentLocator list on;off")
	
if not lx.eval("query scriptsysservice userValue.isdefined ? BVHLoader.applyZeroTransform"):
	lx.eval("user.defNew BVHLoader.applyZeroTransform integer" )
	lx.eval("user.def BVHLoader.applyZeroTransform list on;off")





# test
	#select = lx.evalN("query layerservice polys ? selected")



# file dialog
try:
	lx.eval("dialog.setup fileOpen")
	lx.eval("dialog.title {select files}")
	lx.eval("dialog.fileTypeCustom bvh \"BVH\" \"*.bvh\" bvh")
	
	lx.eval("dialog.open")
	fInputFilePath = lx.eval("dialog.result ?")
	
except:
	lx.out("File read Aborted or some error")
	sys.exit()
	
	
monitor = lx.Monitor()

#read via bvh
bvhRd = BVHReader(fInputFilePath)


# set user values
bvhRd.frameMode = lx.eval("user.value BVHLoader.frameMode ?")
bvhRd.scaleFactor = lx.eval("user.value BVHLoader.scaleFactor ?")
bvhRd.readJointOnly = True if lx.eval("user.value BVHLoader.readJointOnly ?") == "on" else False
bvhRd.rotOrder = lx.eval("user.value BVHLoader.rotOrder ?")
# 	bvhRd.adaptFPS = True if lx.eval("user.value BVHLoader.adaptFPS ?") == "on" else False
bvhRd.rootPin = True if lx.eval("user.value BVHLoader.rootPin ?") == "on" else False
bvhRd.rootPinLimit = lx.eval("user.value BVHLoader.rootPinLimit ?")
bvhRd.createParentLocator = True if lx.eval("user.value BVHLoader.createParentLocator ?") == "on" else False
bvhRd.applyZeroTransform = True if lx.eval("user.value BVHLoader.applyZeroTransform ?") == "on" else False

lx.out(bvhRd.rootPinLimit)

# file name
filesplit = os.path.splitext(os.path.basename(fInputFilePath))
bvhRd.fileName = filesplit[0]

try:
	# suspend undo 
	undoSuspend = True if lx.eval("user.value BVHLoader.undoSuspend ?") == "on" else False
	if undoSuspend == True:
		lx.eval("app.undoSuspend")
except:
	sys.exit()
	
try:
	bvhRd.read()
except SyntaxError:
	lx.out("Syntax Error")
	lx.eval("dialog.setup Error")
	lx.eval("dialog.title {Error}")
	lx.eval("dialog.msg {Syntax Error occured while loading file.}")
	lx.eval("dialog.open")