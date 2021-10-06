from procgame import *

class Info(game.Mode):
	"""Display status report"""
	def __init__(self, game, priority):
		super(Info, self).__init__(game, priority)
		self.title_layer = dmd.TextLayer(128/2, 14, self.game.fonts['tiny7'], "center").set_text("Instant Info")

	def set_layers(self, layers):
		self.layers = [self.title_layer]
		self.layers.extend(layers)
	
	def mode_started(self):
		self.index = 0
		self.index_max = len(self.layers) - 1
		self.update_display()
		
	def sw_flipperLwL_active(self,sw):
		if self.game.switches.flipperLwR.is_active():
			self.progress(-1)

	def sw_flipperLwR_active(self,sw):
		if self.game.switches.flipperLwL.is_active():
			self.progress(1)

	def sw_flipperLwL_inactive(self,sw):
		if self.game.switches.flipperLwR.is_inactive():
			self.exit()

	def sw_flipperLwR_inactive(self,sw):
		if self.game.switches.flipperLwL.is_inactive():
			self.exit()

	def exit(self):
		self.cancel_delayed('delayed_progression')
		self.callback()

	def progress(self, step):
		self.cancel_delayed('delayed_progression')
		self.index += step
		if self.index < 0:
			self.index = self.index_max
		elif self.index > self.index_max:
			self.index = 0
		self.update_display()

	def update_display(self):
		self.layer = self.layers[self.index]
		self.delay(name='delayed_progression', event_type=None, delay=3.0, handler=self.progress, param=1)

