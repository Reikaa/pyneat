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

import time

from Configuration import *
from Genome        import *
from Population    import *
from ExperimentUI  import *

class Run:
   def __init__(self, id, generation):
      self.id         = id
      self.generation = generation

class Experiment:
   def __init__(self, name, start_genes_filename=None, generations=None, ui=ExperimentUI):
      self.name               = name
      self.startGenesFileName = start_genes_filename
      self.generations        = generations
      self.ui                 = ui(self)

      if self.generations is None:
         self.generations = Configuration.numGenerations

   def run(self, useGUI=False):
      if not useGUI:
         self.oldUI = self.ui
         self.ui    = ExperimentConsoleUI(self)

      self.ui.run()

      if not useGUI:
         self.ui = self.oldUI

   def getRuns(self):
      startGenome = Genome(fileName=self.startGenesFileName)

      for i in range(Configuration.numRuns):
         self.population = Population(startGenome)
         for generation in range(self.generations):
            run = Run(i, generation)

            startTime = time.clock()
            self.epoch(generation, run)
            endTime = time.clock()

            run.time = endTime - startTime
            yield run

   def epoch(self, generation, run):
      self.population.epoch(generation, self)

      fitness, outputs, error, won = self.evaluate(self.population.champion.network)

      if won:
         run.winner = self.population.champion.network.id
      else:
         run.winner = None

      run.champion = self.population.champion.network
      run.fitness  = self.population.highestFitness
      run.targets  = self.targets
      run.outputs  = outputs

   def evaluate(self, network):
      raise NotImplementedError, 'Please override the \'evaluate\' method in your experiment class'
