#!/usr/bin/python

"""
pyNEAT
Copyright (C) 2007 Brian Greer

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

## Real-time NEAT test

import Tkinter
import pyNEAT
import random

class Avatar:
   def __init__(self, x, y, map):
      self.map = map

      self.reset(x, y)

      self.directions = [( 0,  0),
                         (-1,  0),
                         (-1, -1),
                         ( 0, -1),
                         ( 1, -1),
                         ( 1,  0),
                         ( 1,  1),
                         ( 0,  1),
                         (-1,  1),
                        ]

   def reset(self, x, y):
      self.x       = x
      self.y       = y
      self.fitness = 0.5
      self.active  = True

   def update(self, network):
      depth = network.getMaxDepth()

      network.clear()
      network.setInput([1.0] + self.map.getGrid(self.x, self.y))
      #network.setInput([1.0] + self.map.map)
      network.activate()
      for i in range(depth):
         network.activate()

      #print network.inputs, network.outputs

      max      = -1
      maxIndex = -1
      for i in range(len(network.outputs)):
         output = network.outputs[i]
         if output.output > max:
            max      = output.output
            maxIndex = i

      if maxIndex >= 0:
         x, y = self.directions[maxIndex]
         self.x, self.y = self.map.move(self.x, self.y, x, y)
         type = self.map.map[self.map.getIndex(self.x, self.y)]
         if type == RTMap.BASE:
            self.active  = False
            self.fitness = 1.0
         elif type == RTMap.MINE:
            self.active  = False
            self.fitness = 0.0

class RTMap:
   START       = 1
   BASE        = 2
   MINE        = 3

   NUM_BASES   = 3
   NUM_MINES   = 6
   NUM_AVATARS = 5

   TIMEOUT     = 50 # TODO: this should not be static; should be determined per generation

   def __init__(self):
      self.width  = 50
      self.height = 50
      self.size   = self.width * self.height

      random.seed()

      self.reset()

   def reset(self):
      self.map = [0 for i in range(self.size)]
      self.map[0]    = RTMap.START
      self.map[1:4]  = RTMap.NUM_BASES * [RTMap.BASE]
      self.map[4:10] = RTMap.NUM_MINES * [RTMap.MINE]

      random.shuffle(self.map)

      for i in range(self.size):
         if self.map[i] == RTMap.START:
            self.startX = i % self.width
            self.startY = i / self.width
            break

      self.population = pyNEAT.Population(pyNEAT.Genome(fileName='rtstartgenes'), RTMap.NUM_AVATARS)
      self.generation = 1
      self.time       = 0
      self.avatars    = [Avatar(self.startX, self.startY, self) for i in range(RTMap.NUM_AVATARS)]

   def update(self):
      regen = False
      self.time += 1

      if self.time >= RTMap.TIMEOUT:
         regen = True
      else:
         regen = True
         for i in range(RTMap.NUM_AVATARS):
            if self.avatars[i].active:
               self.avatars[i].update(self.population.organisms[i].getNetwork())
               regen = False

      if regen:
         self.time = 0
         self.reproduce()

   def reproduce(self):
      self.population.epoch(self.generation, self)
      self.generation += 1

      for avatar in self.avatars:
         avatar.reset(self.startX, self.startY)

   def evaluate(self, network):
      for i in range(RTMap.NUM_AVATARS):
         if self.population.organisms[i].getNetwork().id == network.id:
            fitness = self.avatars[i].fitness
            winner  = (fitness == 1.0)
            error   =  1.0 - fitness
            return fitness, [], error, winner
      return 0.0, [], 0.0, False

   def draw(self, canvas):
      canvasWidth  = canvas.winfo_width()
      canvasHeight = canvas.winfo_height()

      tileWidth    = canvasWidth / self.width
      tileHeight   = canvasHeight / self.height

      for i in range(self.size):
         t = self.map[i]
         if t == RTMap.START:
            x, y = self.getCoords(i, tileWidth, tileHeight)
            self.drawCircle(canvas, x, y, tileWidth, tileHeight)
         elif t == RTMap.BASE:
            x, y = self.getCoords(i, tileWidth, tileHeight)
            self.drawTriangle(canvas, x, y, tileWidth, tileHeight)
         elif t == RTMap.MINE:
            x, y = self.getCoords(i, tileWidth, tileHeight)
            self.drawRectangle(canvas, x, y, tileWidth, tileHeight)

      for avatar in self.avatars:
         if avatar.active:
            i    = self.getIndex(avatar.x, avatar.y)
            x, y = self.getCoords(i, tileWidth, tileHeight)
            self.drawCircle(canvas, x, y, tileWidth, tileHeight, fill='yellow')

   def getCoords(self, i, width, height):
      x = (i % self.width) * width
      y = (i / self.height) * height
      return x, y

   def getIndex(self, x, y):
      return y * self.width + x

   def getGrid(self, x, y):
      i = self.getIndex(x, y)
      if i >= 0 and i < self.size:
         grid = []
         if i >= self.width:
            start = i - self.width
            grid += self.map[start:start + 3]
         else:
            grid += 3 * [-1]
         if i > 0:
            grid.append(self.map[i - 1])
         else:
            grid.append(-1)
         #grid.append(self.map[i])
         if i < (self.size - 1):
            grid.append(self.map[i + 1])
         else:
            grid.append(-1)
         if i < (self.size - self.width):
            start = i + self.width - 1
            grid += self.map[start:start + 3]
         else:
            grid += 3 * [-1]
         return grid
      else:
         return None

   def move(self, x, y, xd, yd):
      newX = x + xd
      newY = y + yd

      i = self.getIndex(newX, newY)

      if i < 0 or i >= self.size or \
         newX < 0 or newX >= self.width:
         return x, y
      else:
         return newX, newY

   def getFitness(self, x, y):
      i = self.getIndex(x, y)
      if self.map[i] == RTMap.BASE:
         return 1.0
      elif self.map[i] == RTMap.MINE:
         return 0.0
      else:
         fitness = 0.5
         grid    = self.getGrid(x, y)
         for x in grid:
            if x == RTMap.MINE:
               fitness -= 0.125
            elif x == RTMap.BASE:
               fitness += 0.25
         return fitness

   def drawCircle(self, canvas, x, y, width, height, fill='black'):
      canvas.create_oval(x, y, x + width, y + height, fill=fill)

   def drawTriangle(self, canvas, x, y, width, height):
      canvas.create_polygon(x, y + height, x + width, y + height, x + width / 2, y, fill='red')

   def drawRectangle(self, canvas, x, y, width, height):
      canvas.create_rectangle(x, y, x + width, y + height, fill='green')

class RTApp:
   def __init__(self):
      self.root = Tkinter.Tk()
      self.root.title('pyNEAT - Real-time Test')
      self.root.geometry('800x600')

      self._addMenus()
      self._addToolBar()
      self._addCanvas()
      self._addStatusBar()

      self.map = RTMap()

      self.pause = False

      self.registerUpdateHandler()

   def _addMenus(self):
      menu = Tkinter.Menu(self.root)
      self.root.config(menu=menu)

      fileMenu = Tkinter.Menu(menu)
      menu.add_cascade(label='File', menu=fileMenu)
      fileMenu.add_command(label='Exit', command=self.root.quit)

   def _addToolBar(self):
      self.toolbar = Tkinter.Frame(self.root)

      self.pauseButton = Tkinter.Button(self.toolbar, text='Pause', width=6, command=self.doPause)
      self.pauseButton.pack(side=Tkinter.LEFT, padx=2, pady=2)

      self.resetButton = Tkinter.Button(self.toolbar, text='Reset', width=6, command=self.doReset)
      self.resetButton.pack(side=Tkinter.LEFT, padx=2, pady=2)

      self.toolbar.pack(side=Tkinter.TOP, fill=Tkinter.X)

   def _addCanvas(self):
      frame = Tkinter.Frame(self.root)
      frame.pack(fill=Tkinter.BOTH, expand=1)

      self.canvas = Tkinter.Canvas(frame, bg='blue')
      self.canvas.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=1)

   def _addStatusBar(self):
      self.status = RTStatusBar(self.root)
      self.status.pack(side=Tkinter.BOTTOM, fill=Tkinter.X)

   def registerUpdateHandler(self):
      self.root.after(100, self.update)

   def update(self):
      self.canvas.delete(Tkinter.ALL)
      self.map.draw(self.canvas)
      self.canvas.update_idletasks()
      if not self.pause:
         self.registerUpdateHandler()
      self.map.update()

   def doPause(self):
      self.pause = not self.pause
      if self.pause:
         self.pauseButton.config(text='Run')
      else:
         self.pauseButton.config(text='Pause')
         self.registerUpdateHandler()

   def doReset(self):
      self.map.reset()

   def run(self):
      self.root.mainloop()

class RTStatusBar(Tkinter.Frame):
   def __init__(self, master):
      Tkinter.Frame.__init__(self, master)

      self.label = self._makeLabel('Status')

   def _makeLabel(self, text):
      label = Tkinter.Label(self, text=text, bd=1, relief=Tkinter.SUNKEN, anchor=Tkinter.W)
      label.pack(side=Tkinter.LEFT, fill=Tkinter.X, expand=1)
      return label

   def _setLabel(self, label, text):
      label.config(text=text)
      label.update_idletasks()

if __name__ == '__main__':
   pyNEAT.loadConfiguration('rt.ne')
   app = RTApp()
   app.run()
