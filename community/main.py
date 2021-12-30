import logging
import random
import time
import os

import pyglet

pyglet.options["shadow_window"] = False
pyglet.options["debug_gl"] = False
pyglet.options["search_local_libs"] = True
pyglet.options["audio"] = ("openal", "pulse", "directsound", "xaudio2", "silent")

import pyglet.gl as gl

import shader
import camera
import texture_manager

import world

import hit
import time

import joystick
import keyboard_mouse

class Window(pyglet.window.Window):
	def __init__(self, **args):
		super().__init__(**args)
		
		# create shader

		logging.info("Compiling Shaders")
		self.shader = shader.Shader("vert.glsl", "frag.glsl")
		self.shader_sampler_location = self.shader.find_uniform(b"u_TextureArraySampler")
		self.shader.use()

		# create textures
		logging.info("Creating Texture Array")
		self.texture_manager = texture_manager.TextureManager(16, 16, 256)

		# camera stuff

		logging.info("Setting up camera scene")
		self.camera = camera.Camera(self.shader, self.width, self.height)

		# create world

		self.world = world.World(self.shader, self.camera, self.texture_manager)

		# pyglet stuff

		pyglet.clock.schedule(self.update)
		pyglet.clock.schedule_interval(self.tick, 1 / 60)
		pyglet.clock.schedule_interval(self.world.update_time, 1)
		self.mouse_captured = False

		# misc stuff

		self.holding = 50

		# bind textures

		gl.glActiveTexture(gl.GL_TEXTURE0)
		gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self.world.texture_manager.texture_array)
		gl.glUniform1i(self.shader_sampler_location, 0)

		# enable cool stuff

		gl.glEnable(gl.GL_DEPTH_TEST)
		gl.glEnable(gl.GL_CULL_FACE)
		gl.glBlendFunc(gl.GL_SRC_COLOR, gl.GL_ONE_MINUS_SRC_COLOR)

		# controls stuff
		self.controls = [0, 0, 0]

		# joystick stuff
		self.joystick_controller = joystick.Joystick_controller(self)

		# mouse and keyboard stuff
		self.keyboard_mouse = keyboard_mouse.Keyboard_Mouse(self)

		# music stuff
		logging.info("Loading audio")
		self.music = [pyglet.media.load(os.path.join("audio/music", file)) for file in os.listdir("audio/music") if os.path.isfile(os.path.join("audio/music", file))]

		self.player = pyglet.media.Player()
		self.player.volume = 0.5

		if len(self.music) > 0:
			self.player.queue(random.choice(self.music))
			self.player.play()
			self.player.standby = False
		else:
			self.player.standby = True

		self.player.next_time = 0

	def on_close(self):
		logging.info("Deleting player")
		self.player.delete()

		pyglet.app.exit() # Closes the game

	def tick(self, delta_time):
		if not self.player.source and len(self.music) > 0:
			if not self.player.standby:
				self.player.standby = True
				self.player.next_time = time.time() + random.randint(240, 360)
			elif time.time() >= self.player.next_time:
				self.player.standby = False
				self.player.queue(random.choice(self.music))
				self.player.play()
				
		self.world.tick()

	def update(self, delta_time):
		if pyglet.clock.get_fps() < 20:
			logging.warning(f"Warning: framerate dropping below 20 fps ({pyglet.clock.get_fps()} fps)")

		if not self.mouse_captured:
			self.camera.input = [0, 0, 0]

		self.joystick_controller.update_controller()
		self.camera.update_camera(delta_time)
		self.world.update()
	
	def on_draw(self):
		self.camera.update_matrices()

		self.clear()

		self.world.draw()

		gl.glFinish()

	# input functions

	def on_resize(self, width, height):
		logging.info(f"Resize {width} * {height}")
		gl.glViewport(0, 0, width, height)

		self.camera.width = width
		self.camera.height = height

class Game:
	def __init__(self):
		self.config = gl.Config(double_buffer = True,
				major_version = 4, minor_version = 6,
				depth_size = 16)
		self.window = Window(config = self.config, width = 854, height = 480, caption = "Minecraft clone", resizable = True, vsync = False)

	def run(self): 
		pyglet.app.run()



def init_logger():
	log_folder = "logs/"
	log_filename = f"{time.time()}.log"
	log_path = os.path.join(log_folder, log_filename)

	if not os.path.isdir(log_folder):
		os.mkdir(log_folder)

	with open(log_path, 'x') as file:
		file.write("[LOGS]\n")

	logging.basicConfig(level=logging.INFO, filename=log_path, 
		format="[%(asctime)s] [%(processName)s/%(threadName)s/%(levelname)s] (%(module)s.py/%(funcName)s) %(message)s")




def main():
	init_logger()
	game = Game()
	game.run()

if __name__ == "__main__":
	main()