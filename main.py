from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import hex_colormap, colormap
from kivy.animation import Animation
from kivy.metrics import sp, dp
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy import platform
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, ListProperty, StringProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import SlideTransition, FadeTransition, SwapTransition
from kivy.graphics import Color, Ellipse, PushMatrix, PopMatrix, Translate, Rectangle
from kivy.graphics.context_instructions import Color as ColorInstruction
import io
import os
import random
import time
import math
from kivy.core.audio import SoundLoader

# Global particle toggle (can be toggled in Settings)
PARTICLES_ENABLED = True

# Create simple test audio if no files exist
def create_test_audio():
    """Create a simple test audio file if none exist"""
    import wave
    import struct
    
    test_files = ['audios/key1.mp3', 'audios/key2.mp3', 'audios/key3.mp3']
    if any(os.path.exists(f) for f in test_files):
        return  # Files already exist
    
    # Create a simple WAV file as fallback
    try:
        wav_path = 'audios/test.wav'
        if not os.path.exists(wav_path):
            # Generate a simple sine wave
            sample_rate = 44100
            duration = 2.0
            frequency = 440  # A4 note
            
            frames = int(sample_rate * duration)
            with wave.open(wav_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)   # 16-bit
                wav_file.setframerate(sample_rate)
                
                for i in range(frames):
                    value = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                    wav_file.writeframes(struct.pack('<h', value))
            
            print(f"Created test audio: {wav_path}")
    except Exception as e:
        print(f"Failed to create test audio: {e}")

# Background music manager
class BackgroundMusic:
    def __init__(self):
        self.current_sound = None
        # Use absolute paths
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.track_list = [
            os.path.join(self.base_dir, 'audios', 'key1.mp3'),
            os.path.join(self.base_dir, 'audios', 'key2.mp3'),
            os.path.join(self.base_dir, 'audios', 'key3.mp3')
        ]
        self.current_index = None
        self.volume = 1.0  # Maximum volume by default
        self.enabled = True
        # Shuffle track order on startup
        self.shuffle_order()
        self.load_next_track()
    
    def shuffle_order(self):
        """Create random play order"""
        self.play_order = list(range(len(self.track_list)))
        random.shuffle(self.play_order)
        self.current_position = -1
        print(f"Track order: {[os.path.basename(self.track_list[i]) for i in self.play_order]}")
    
    def load_next_track(self):
        if not self.enabled:
            return
        # Get next track in shuffled order
        self.current_position = (self.current_position + 1) % len(self.play_order)
        self.current_index = self.play_order[self.current_position]
        track_path = self.track_list[self.current_index]
        
        print(f"Trying to load: {track_path}")
        print(f"File exists: {os.path.exists(track_path)}")
        print(f"Current directory: {os.getcwd()}")
        
        # Check if file exists before loading
        if os.path.exists(track_path):
            self.current_sound = SoundLoader.load(track_path)
            if self.current_sound:
                self.current_sound.volume = self.volume
                self.current_sound.bind(on_stop=self.on_track_finished)
                self.current_sound.play()
                print(f"Playing: {os.path.basename(track_path)}")
            else:
                print(f"Failed to load: {os.path.basename(track_path)}")
                self.current_sound = None
                # Try next track after delay
                Clock.schedule_once(lambda dt: self.load_next_track(), 2.0)
        else:
            print(f"Audio file not found: {os.path.basename(track_path)}")
            self.current_sound = None
            # Try next track after delay
            Clock.schedule_once(lambda dt: self.load_next_track(), 2.0)
    
    def on_track_finished(self, instance):
        # Load next random track when current ends
        self.load_next_track()
    
    def set_volume(self, vol):
        self.volume = max(0, min(1, vol))
        if self.current_sound:
            self.current_sound.volume = self.volume
    
    def stop(self):
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound.unbind(on_stop=self.on_track_finished)
            self.current_sound = None

# Global music instance
create_test_audio()
bg_music = BackgroundMusic()


# Класс для красивых частиц с градиентом
class Particle(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    size = NumericProperty(dp(8))
    lifetime = NumericProperty(3.0)
    age = NumericProperty(0)
    color1 = ListProperty([1, 1, 1, 0.8])  # Start color
    color2 = ListProperty([0.5, 0.8, 1, 0.3])  # End color
    particle_type = StringProperty('bubble')  # bubble, star, spark
    
    def __init__(self, particle_type='bubble', x=None, y=None, **kwargs):
        super().__init__(**kwargs)
        self.particle_type = particle_type
        self.size_hint = None, None
        
        if particle_type == 'bubble':
            self._create_bubble(x, y)
        elif particle_type == 'star':
            self._create_star(x, y)
        elif particle_type == 'spark':
            self._create_spark(x, y)
        
        # Disable touch handling
        self.disabled = True
    
    def _create_bubble(self, x=None, y=None):
        size = random.randint(6, 12)
        self.width = dp(size)
        self.height = dp(size)
        self.velocity_x = random.uniform(-1, 1)
        self.velocity_y = random.uniform(1, 3)
        self.lifetime = random.uniform(4, 8)
        
        # Gradient colors for bubble
        self.color1 = [0.8, 0.9, 1.0, 0.6]
        self.color2 = [0.4, 0.7, 0.9, 0.2]
        
        window_width = getattr(Window, 'width', 450) or 450
        window_height = getattr(Window, 'height', 900) or 900
        
        if x is not None and y is not None:
            self.pos = (x, y)
        else:
            self.pos = (random.randint(0, int(window_width)), 
                       random.randint(0, int(window_height)))
        
        with self.canvas:
            # Outer glow
            Color(*self.color1)
            self.outer = Ellipse(pos=self.pos, size=(self.width, self.height))
            # Inner highlight
            Color(*self.color2)
            self.inner = Ellipse(pos=(self.pos[0] + self.width*0.2, 
                                       self.pos[1] + self.height*0.2), 
                                  size=(self.width*0.4, self.height*0.4))
    
    def _create_star(self, x=None, y=None):
        size = random.randint(4, 10)
        self.width = dp(size)
        self.height = dp(size)
        self.velocity_x = random.uniform(-0.5, 0.5)
        self.velocity_y = random.uniform(-0.5, 0.5)
        self.lifetime = random.uniform(2, 4)
        
        # Gradient colors for star
        self.color1 = [1.0, 1.0, 0.8, 0.9]
        self.color2 = [1.0, 0.8, 0.4, 0.3]
        
        window_width = getattr(Window, 'width', 450) or 450
        window_height = getattr(Window, 'height', 900) or 900
        
        if x is not None and y is not None:
            self.pos = (x, y)
        else:
            self.pos = (random.randint(0, int(window_width)), 
                       random.randint(0, int(window_height)))
        
        with self.canvas:
            Color(*self.color1)
            self.star = Ellipse(pos=self.pos, size=(self.width, self.height))
    
    def _create_spark(self, x=None, y=None):
        size = random.randint(2, 6)
        self.width = dp(size)
        self.height = dp(size)
        self.velocity_x = random.uniform(-2, 2)
        self.velocity_y = random.uniform(-2, 2)
        self.lifetime = random.uniform(1, 3)
        
        # Gradient colors for spark
        self.color1 = [1.0, 0.9, 0.7, 1.0]
        self.color2 = [1.0, 0.4, 0.2, 0.2]
        
        window_width = getattr(Window, 'width', 450) or 450
        window_height = getattr(Window, 'height', 900) or 900
        
        if x is not None and y is not None:
            self.pos = (x, y)
        else:
            self.pos = (random.randint(0, int(window_width)), 
                       random.randint(0, int(window_height)))
        
        with self.canvas:
            Color(*self.color1)
            self.spark = Ellipse(pos=self.pos, size=(self.width, self.height))
    
    def _create_yellow(self, x=None, y=None):
        size = random.randint(4, 8)
        self.width = dp(size)
        self.height = dp(size)
        self.velocity_x = random.uniform(-1.5, 1.5)
        self.velocity_y = random.uniform(-1.5, 1.5)
        self.lifetime = random.uniform(2, 4)
        
        # Gradient colors for yellow particle with #2D8FB5
        self.color1 = [0.176, 0.562, 0.710, 0.9]  # #2D8FB5
        
        window_width = getattr(Window, 'width', 450) or 450
        window_height = getattr(Window, 'height', 900) or 900
        
        if x is not None and y is not None:
            self.pos = (x, y)
        else:
            self.pos = (random.randint(0, int(window_width)), 
                       random.randint(0, int(window_height)))
        
        with self.canvas:
            # Outer glow with blue color
            Color(*self.color1)
            self.outer = Ellipse(pos=self.pos, size=(self.width, self.height))
            # Inner highlight with yellow
            Color(*self.color2)
            self.inner = Ellipse(pos=(self.pos[0] + self.width*0.2, 
                                       self.pos[1] + self.height*0.2), 
                                  size=(self.width*0.4, self.height*0.4))
    
    def on_touch_down(self, touch):
        return False
    
    def update(self, dt):
        self.age += dt
        if self.age > self.lifetime:
            return False
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Add physics based on particle type
        if self.particle_type == 'bubble':
            # Float up with wobble
            self.velocity_x += random.uniform(-0.1, 0.1)
            self.velocity_x = max(-2, min(2, self.velocity_x))
        elif self.particle_type == 'star':
            # Twinkle and slow drift
            self.x += math.sin(self.age * 3) * 0.3
            self.y += math.cos(self.age * 2) * 0.2
        elif self.particle_type == 'spark':
            # Fast movement with fade
            self.velocity_y -= 0.1  # Slight gravity
        
        # Update visual positions
        if self.particle_type == 'bubble':
            self.outer.pos = self.pos
            self.outer.size = (self.width, self.height)
            self.inner.pos = (self.pos[0] + self.width*0.2, 
                           self.pos[1] + self.height*0.2)
            self.inner.size = (self.width*0.4, self.height*0.4)
        else:
            if hasattr(self, 'star'):
                self.star.pos = self.pos
                self.star.size = (self.width, self.height)
            elif hasattr(self, 'spark'):
                self.spark.pos = self.pos
                self.spark.size = (self.width, self.height)
        
        # Fade out near end of life
        fade_start = self.lifetime * 0.7
        if self.age > fade_start:
            alpha = 1.0 - (self.age - fade_start) / (self.lifetime - fade_start)
            for instruction in self.canvas.children:
                if isinstance(instruction, (Color, ColorInstruction)):
                    if instruction.rgba[3] > 0.5:
                        instruction.rgba = (*self.color1[:3], self.color1[3] * alpha)
                    else:
                        instruction.rgba = (*self.color2[:3], self.color2[3] * alpha)
        
        return True


# Класс для частиц всплеска при клике
class SplashParticle(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    size = NumericProperty(dp(5))
    lifetime = NumericProperty(1.0)
    age = NumericProperty(0)
    
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = None, None
        particle_size = random.randint(3, 7)
        self.width = dp(particle_size)
        self.height = dp(particle_size)
        angle = random.uniform(0, 2 * 3.14159)
        speed = random.uniform(1.2, 3.0)
        self.velocity_x = speed * math.cos(angle)
        self.velocity_y = speed * math.sin(angle)
        self.lifetime = random.uniform(0.9, 1.8)
        self.pos = (x, y)
        
        # Disable touch handling for particles
        self.disabled = True
        
        # Create splash particle visual
        with self.canvas:
            # slightly softer, more readable splash color
            Color(0.6, 0.85, 1, 0.8)
            self.particle = Ellipse(pos=self.pos, size=(self.width, self.height))
    
    def on_touch_down(self, touch):
        # Particles should never handle touch events
        return False
    
    def update(self, dt):
        self.age += dt
        if self.age > self.lifetime:
            return False
        
        # Update position with gravity
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y -= 0.7  # Softer gravity effect
        
        # Update visual
        self.particle.pos = self.pos
        self.particle.size = (self.width, self.height)
        
        return True


# Класс для дальних пузырей (глубина)
class DeepBubble(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    size = NumericProperty(dp(3))
    lifetime = NumericProperty(8.0)
    age = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = None, None
        bubble_size = random.randint(2, 4)
        self.width = dp(bubble_size)
        self.height = dp(bubble_size)
        self.velocity_x = random.uniform(-0.3, 0.3)
        self.velocity_y = random.uniform(0.5, 1.5)
        self.lifetime = random.uniform(6, 12)
        window_width = getattr(Window, 'width', 450) or 450
        window_height = getattr(Window, 'height', 900) or 900
        self.pos = (random.randint(0, int(window_width)), -dp(10))
        self.disabled = True
        
        with self.canvas:
            Color(0.7, 0.85, 1, 0.2)
            self.bubble = Ellipse(pos=self.pos, size=(self.width, self.height))
    
    def on_touch_down(self, touch):
        return False
    
    def update(self, dt):
        self.age += dt
        if self.age > self.lifetime:
            return False
        
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_x += random.uniform(-0.05, 0.05)
        self.velocity_x = max(-0.5, min(0.5, self.velocity_x))
        
        self.bubble.pos = self.pos
        self.bubble.size = (self.width, self.height)
        
        fade_start = self.lifetime * 0.8
        if self.age > fade_start:
            alpha = 1.0 - (self.age - fade_start) / (self.lifetime - fade_start)
            for instruction in self.canvas.children:
                if isinstance(instruction, (Color, ColorInstruction)):
                    instruction.rgba = (0.7, 0.85, 1, 0.2 * alpha)
        
        return True


# Класс для пузырьковых частиц
class Bubble(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    size = NumericProperty(dp(10))
    lifetime = NumericProperty(5.0)
    age = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = None, None
        bubble_size = random.randint(5, 15)
        self.width = dp(bubble_size)
        self.height = dp(bubble_size)
        self.velocity_x = random.uniform(-1, 1)
        self.velocity_y = random.uniform(1, 3)
        self.lifetime = random.uniform(3, 8)
        # Use safe window size access
        window_width = getattr(Window, 'width', 450) or 450
        window_height = getattr(Window, 'height', 900) or 900
        self.pos = (random.randint(0, int(window_width)), 
                   random.randint(0, int(window_height)))
        
        # Disable touch handling for bubbles
        self.disabled = True
        
        # Create bubble visual
        with self.canvas:
            Color(1, 1, 1, 0.3)
            self.bubble = Ellipse(pos=self.pos, size=(self.width, self.height))
            Color(0.8, 0.9, 1, 0.2)
            self.highlight = Ellipse(pos=(self.pos[0] + self.width*0.2, 
                                       self.pos[1] + self.height*0.2), 
                                  size=(self.width*0.3, self.height*0.3))
    
    def on_touch_down(self, touch):
        # Bubbles should never handle touch events
        return False
    
    def update(self, dt):
        self.age += dt
        if self.age > self.lifetime:
            return False
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Add slight wobble
        self.velocity_x += random.uniform(-0.1, 0.1)
        self.velocity_x = max(-2, min(2, self.velocity_x))
        
        # Update visual
        self.bubble.pos = self.pos
        self.bubble.size = (self.width, self.height)
        self.highlight.pos = (self.pos[0] + self.width*0.2, 
                             self.pos[1] + self.height*0.2)
        self.highlight.size = (self.width*0.3, self.height*0.3)
        
        # Fade out near end of life
        fade_start = self.lifetime * 0.7
        if self.age > fade_start:
            alpha = 1.0 - (self.age - fade_start) / (self.lifetime - fade_start)
            # Get the Color instructions from canvas
            for instruction in self.canvas.children:
                if isinstance(instruction, (Color, ColorInstruction)):
                    if instruction.rgba[3] > 0.5:  # Main bubble color
                        instruction.rgba = (1, 1, 1, 0.3 * alpha)
                    else:  # Highlight color
                        instruction.rgba = (0.8, 0.9, 1, 0.2 * alpha)
        
        return True


# Класс для управления временем и анимациями
class TimeManager:
    time = 0
    
    @staticmethod
    def update(dt):
        TimeManager.time += dt


class Menu(Screen):
    particles = ListProperty([])
    splash_particles = ListProperty([])
    particle_container = ObjectProperty(None)
    
    def __init__(self, **kw):
        super().__init__(**kw)
        # Create particle container
        self.particle_container = Widget()
        self.add_widget(self.particle_container, index=0)  # Add at bottom
        
        # Start particle systems
        Clock.schedule_interval(self.update_particles, 1/30.0)
        Clock.schedule_interval(self.spawn_particle, 0.4)
    
    def on_touch_down(self, touch):
        # Create splash particles at touch position
        if not self.collide_point(*touch.pos):
            return
        self.create_splash(touch.x, touch.y)
        return super(Menu, self).on_touch_down(touch)
    
    def create_splash(self, x, y):
        # Create splash particles at click position
        for _ in range(random.randint(8, 12)):
            particle_type = random.choice(['bubble', 'star', 'spark'])
            particle = Particle(particle_type, x=x, y=y)
            self.particle_container.add_widget(particle)
            self.splash_particles.append(particle)
    
    def update_particles(self, dt):
        # Update time manager
        TimeManager.update(dt)
        
        # Update existing particles
        particles_to_remove = []
        for particle in self.particles:
            if not particle.update(dt):
                particles_to_remove.append(particle)
                self.particle_container.remove_widget(particle)
        
        for particle in particles_to_remove:
            self.particles.remove(particle)
        
        # Update existing splash particles
        splash_to_remove = []
        for particle in self.splash_particles:
            if not particle.update(dt):
                splash_to_remove.append(particle)
                self.particle_container.remove_widget(particle)
        
        for particle in splash_to_remove:
            self.splash_particles.remove(particle)
    
    def spawn_particle(self, dt):
        if len(self.particles) < 20:  # Limit particle count
            particle_type = random.choice(['bubble', 'star', 'spark'])
            particle = Particle(particle_type)
            self.particle_container.add_widget(particle)
            self.particles.append(particle)

    # Перехід до екрана гри
    def go_game(self, *args):
        # Smooth slide transition to game
        self.manager.transition = SlideTransition(direction='left', duration=0.5)
        self.manager.current = "game"

    # Перехід до екрана налаштувань
    def go_settings(self, *args):
        # Smooth slide transition to settings
        self.manager.transition = SlideTransition(direction='up', duration=0.4)
        self.manager.current = "settings"

    # Вихід з програми
    def exit_app(self, *args):
        app.stop()


class Settings(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Повернення до меню
    def go_menu(self, *args):
        # Smooth slide transition back to menu
        self.manager.transition = SlideTransition(direction='down', duration=0.4)
        self.manager.current = "menu"


# Клас для обертання картинок; в класі, який спадковує потрібно дадати властивість angle
class RotatedImage(Image):
    ...


# КЛАС РИБИ: Обробка кліків, створення "нової" риби
class Fish(RotatedImage):
    # Властивість для забезпечення програвання однієї анімації в один проміжок часу
    anim_play = False
    interaction_block = True
    COEF_MULT = 1.5
    fish_current = None
    fish_index = 0
    hp_current = NumericProperty(0)
    max_hp = NumericProperty(0)
    angle = NumericProperty(0)
    scale = NumericProperty(1.0)
    is_clicked = BooleanProperty(False)
    combo_hits = ListProperty([])

    def on_kv_post(self, base_widget):
        # Find the Game screen (parent of parent of parent)
        current = self.parent
        while current and not hasattr(current, 'score'):
            current = current.parent
        self.GAME_SCREEN = current

        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]['source']
        self.max_hp = app.FISHES[self.fish_current]['hp']
        self.hp_current = self.max_hp

        self.swim()

    def swim(self):
        # Simple appearance animation
        self.pos = (-self.width, self.GAME_SCREEN.height / 2 - self.height / 2)
        self.opacity = 0
        self.scale = 0.5
        self.angle = 0
        
        target_x = self.GAME_SCREEN.width / 2 - self.width / 2
        
        # Simplified: slide in with fade and scale
        swim = Animation(x=target_x, opacity=1, scale=1.0, duration=0.6, t='out_quad')
        swim.start(self)
        
        def _on_swim_complete(*args):
            self.interaction_block = False
            # Start idle sway only if not defeated
            if self.hp_current > 0:
                self._start_idle_sway()

        swim.bind(on_complete=_on_swim_complete)
    
    def _start_idle_sway(self):
        # Stop any existing idle animation
        if hasattr(self, '_idle_anim'):
            try:
                self._idle_anim.cancel(self)
            except Exception:
                pass
        # Start gentle idle sway with stronger pulse
        sway = Animation(angle=2, duration=1.2, t='in_out_sine') + \
               Animation(angle=-2, duration=1.2, t='in_out_sine')
        pulse = Animation(scale=1.08, duration=0.8, t='in_out_sine') + \
                Animation(scale=1.0, duration=0.8, t='in_out_sine')
        idle = sway & pulse
        idle.repeat = True
        idle.start(self)
        self._idle_anim = idle

    # Перемогли рибу :)
    def defeated(self):
        self.interaction_block = True
        # Stop idle sway if running
        if hasattr(self, '_idle_anim'):
            try:
                self._idle_anim.cancel(self)
            except Exception:
                pass
            self.angle = 0
        # Simple minimalist defeat - just fade out
        anim = Animation(opacity=0, duration=0.3)
        anim.start(self)

    # КЛІК!
    def on_touch_down(self, touch):
        # Check if touch is on buttons first (buttons have priority)
        if self._is_touch_on_buttons(touch):
            return False  # Let buttons handle the touch
        
        # Fish is clickable everywhere else on the game screen
        if not self.interaction_block and not self.anim_play:
            # Stop idle sway during click
            if hasattr(self, '_idle_anim'):
                try:
                    self._idle_anim.cancel(self)
                except Exception:
                    pass
            # Start click animation
            self.anim_play = True
            self.interaction_block = True
            
            # Simple scale pulse animation
            anim = Animation(scale=1.2, duration=0.1) + Animation(scale=1.0, duration=0.1)
            anim.bind(on_complete=self._on_click_complete)
            anim.start(self)
            return True
        return super().on_touch_down(touch)
    
    def _is_touch_on_buttons(self, touch):
        """Check if touch is on any button area"""
        # Get game screen dimensions
        game_screen = self.parent.parent  # Navigate to Game screen
        
        # Top menu area (where home button is) - check if touch is in this area
        top_menu_height = Window.height * 0.12
        if touch.y > Window.height - top_menu_height:
            # Check if touch is near the home button area (top right)
            home_button_area = Window.width * 0.2  # Right 20% of screen
            if touch.x > Window.width - home_button_area:
                return True
        
        # Bottom menu area (where settings button is) - check if touch is in this area
        bottom_menu_height = Window.height * 0.12
        if touch.y < bottom_menu_height:
            # Check if touch is near the settings button area (bottom left)
            settings_button_area = Window.width * 0.3  # Left 30% of screen
            if touch.x < settings_button_area:
                return True
        
        return False
    
    def _on_click_complete(self, *args):
        self.hp_current -= 1
        self.is_clicked = False
        # Detect combo
        is_combo = self.GAME_SCREEN.register_hit()
        # Update score
        if is_combo:
            self.GAME_SCREEN.score += 2
        else:
            self.GAME_SCREEN.score += 1
        # Create splash at fish position
        self.GAME_SCREEN.create_splash(self.center_x, self.center_y)
        # Show score popup with combo detection
        self.GAME_SCREEN.show_score_popup(self.center_x, self.center_y, combo=is_combo)
        # Blue flash on hit
        flash = Animation(color=(0.2, 0.5, 1, 1), duration=0.1) + Animation(color=(1, 1, 1, 1), duration=0.2)
        flash.start(self)
        if self.hp_current <= 0:
            # Defeated animation: swim out
            self.anim_play = True
            self.interaction_block = True
            defeated = Animation(x=self.GAME_SCREEN.width, duration=0.8, t='in_quad')
            defeated.start(self)
            Clock.schedule_once(self._on_defeated_complete, 0.8)
        else:
            # Reset animation state and restart idle sway
            self.anim_play = False
            self.interaction_block = False
            self._start_idle_sway()
    
    def _on_defeated_complete(self, *args):
        self._spawn_next_fish(0)
    
    def _spawn_next_fish(self, dt):
        # Check if there are more fish in the level
        current_level = app.LEVELS[app.LEVEL]
        if self.fish_index < len(current_level) - 1:
            self.fish_index += 1
            # Reset animation states
            self.anim_play = False
            self.interaction_block = True
            self.new_fish()
        else:
            # Level complete
            Clock.schedule_once(self.GAME_SCREEN.level_complete, 0.1)


class Game(Screen):
    score = NumericProperty(0)
    splash_particles = ListProperty([])
    deep_particles = ListProperty([])
    particle_container = ObjectProperty(None)
    deep_container = ObjectProperty(None)
    combo_timer = NumericProperty(0)
    combo_count = NumericProperty(0)

    def on_pre_enter(self, *args):
        self.score = 0
        app.LEVEL = 0
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0

        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()
        self.load_gif_background()
        # Create particle container
        self.particle_container = Widget()
        self.add_widget(self.particle_container, index=0)  # Add at bottom
        # Create deep background particle container
        self.deep_container = Widget()
        self.add_widget(self.deep_container, index=0)  # Bottom-most layer
        # Bind window resize to update GIF size
        Window.bind(on_resize=self.on_window_resize)
        # Start particle system
        Clock.schedule_interval(self.update_particles, 1/30.0)
        if PARTICLES_ENABLED:
            Clock.schedule_interval(self.spawn_deep_bubble, 1.5)
            Clock.schedule_interval(self.update_combo, 0.1)
        return super().on_enter(*args)
    
    def on_touch_down(self, touch):
        # Create splash particles at touch position (except on fish)
        if not self.collide_point(*touch.pos):
            return
        
        # Check if touch is on fish
        fish_widget = self.ids.fish
        if fish_widget.collide_point(*touch.pos):
            return super(Game, self).on_touch_down(touch)
        
        # Create splash at touch position
        self.create_splash(touch.x, touch.y)
        return super(Game, self).on_touch_down(touch)
    
    def update_particles(self, dt):
        # Update existing splash particles
        particles_to_remove = []
        for particle in self.splash_particles:
            if not particle.update(dt):
                particles_to_remove.append(particle)
                self.particle_container.remove_widget(particle)
        
        for particle in particles_to_remove:
            self.splash_particles.remove(particle)
        
        # Update deep background particles
        if PARTICLES_ENABLED:
            deep_to_remove = []
            for particle in self.deep_particles:
                if not particle.update(dt):
                    deep_to_remove.append(particle)
                    self.deep_container.remove_widget(particle)
            for particle in deep_to_remove:
                self.deep_particles.remove(particle)
    
    def create_splash(self, x, y):
        if not PARTICLES_ENABLED:
            return
        # Create splash particles at click position
        for _ in range(random.randint(8, 15)):
            particle = SplashParticle(x, y)
            self.particle_container.add_widget(particle)
            self.splash_particles.append(particle)
    
    def show_score_popup(self, x, y, combo=False):
        text = f"+{'2' if combo else '1'}"
        color = (0.3, 1, 1, 1) if combo else (1, 0.95, 0.4, 1)
        label = Label(text=text, font_size=sp(40), color=color)
        label.size_hint = (None, None)
        label.texture_update()
        label.size = label.texture_size
        label.pos = (x - label.width / 2, y)
        self.add_widget(label)

        # Simpler, smoother animation
        start_y = y
        end_y = y + dp(100)
        start_size = sp(52)
        end_size = sp(40)
        
        # Combined animation: move up + shrink + fade
        anim = Animation(y=end_y, font_size=end_size, opacity=0, duration=0.8, t='out_quad')
        anim.start(label)
        anim.bind(on_complete=lambda *args: self.remove_widget(label))
        
        if combo:
            combo_label = Label(text="COMBO x2", font_size=sp(32), color=(0.3, 1, 1, 1))
            combo_label.size_hint = (None, None)
            combo_label.texture_update()
            combo_label.size = combo_label.texture_size
            combo_label.pos = (x - combo_label.width / 2, y + dp(30))
            combo_label.opacity = 0
            self.add_widget(combo_label)
            # Fade in then fade out
            anim_combo_in = Animation(opacity=1, duration=0.2)
            anim_combo_out = Animation(y=y + dp(120), opacity=0, duration=0.6, t='out_quad')
            anim_combo_in.bind(on_complete=lambda *args: anim_combo_out.start(combo_label))
            anim_combo_out.bind(on_complete=lambda *args: self.remove_widget(combo_label))
            anim_combo_in.start(combo_label)
    
    def on_window_resize(self, instance, width, height):
        # Update GIF size and position when window is resized
        if hasattr(self, 'ids') and 'gif_background' in self.ids:
            # Set size to match window
            self.ids.gif_background.size = (width, height)
            # Ensure position is at (0,0)
            self.ids.gif_background.pos = (0, 0)
            # Force texture update
            if hasattr(self, 'gif_frames') and self.gif_frames:
                self.ids.gif_background.texture = self.gif_frames[self.current_gif_frame % len(self.gif_frames)]

    def load_gif_background(self):
        try:
            print("Loading GIF background...")
            # Load GIF using PIL and create textures in memory
            from PIL import Image as PILImage
            from kivy.graphics.texture import Texture
            import os
            
            # Get absolute path to GIF file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            gif_path = os.path.join(script_dir, 'assets', '123123.gif')
            
            if not os.path.exists(gif_path):
                print(f"GIF file not found: {gif_path}")
                return
            
            gif = PILImage.open(gif_path)
            self.gif_frames = []
            self.current_gif_frame = 0
            
            print(f"GIF has {gif.n_frames} frames")
            
            # Create textures for all frames
            for frame in range(gif.n_frames):
                gif.seek(frame)
                img = gif.convert('RGBA')
                # Flip the image horizontally and vertically
                img = img.transpose(PILImage.FLIP_LEFT_RIGHT)
                img = img.transpose(PILImage.FLIP_TOP_BOTTOM)
                
                # Create high-quality texture
                texture = Texture.create(size=img.size, colorfmt='rgba', mipmap=True)
                texture.blit_buffer(img.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
                texture.mag_filter = 'linear'
                texture.min_filter = 'linear'
                self.gif_frames.append(texture)
            
            print(f"Loaded {len(self.gif_frames)} frames")
            
            # Set first frame
            if self.gif_frames:
                self.ids.gif_background.texture = self.gif_frames[0]
                # Set size to fill entire screen completely
                self.ids.gif_background.size = (Window.width, Window.height)
                self.ids.gif_background.pos = (0, 0)
                # Adjust texture coordinates to cover entire image
                self.ids.gif_background.tex_coords = (0, 0, 1, 0, 1, 1, 0, 1)
                print("GIF background loaded successfully")
            
            # Start animation
            Clock.schedule_once(self.animate_gif_direct, 0.1)
        except Exception as e:
            print(f"Error loading GIF background: {e}")

    def animate_gif_direct(self, dt):
        if hasattr(self, 'gif_frames') and self.gif_frames:
            self.current_gif_frame = (self.current_gif_frame + 1) % len(self.gif_frames)
            self.ids.gif_background.texture = self.gif_frames[self.current_gif_frame]
            Clock.schedule_once(self.animate_gif_direct, 0.1)

    def start_game(self):
        self.ids.fish.new_fish()

    def spawn_deep_bubble(self, dt):
        if not PARTICLES_ENABLED:
            return
        if len(self.deep_particles) < 25:
            bubble = DeepBubble()
            self.deep_container.add_widget(bubble)
            self.deep_particles.append(bubble)
    
    def update_combo(self, dt):
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_count = 0
    
    def register_hit(self):
        now = time.time()
        if hasattr(self, '_last_hit_time') and now - self._last_hit_time < 1.2:
            self.combo_count += 1
            self.combo_timer = 1.2
        else:
            self.combo_count = 1
            self.combo_timer = 1.2
        self._last_hit_time = now
        return self.combo_count >= 3
    
    def level_complete(self, *args):
        # Create big bubble burst on level complete
        if PARTICLES_ENABLED:
            for _ in range(30):
                bubble = DeepBubble()
                bubble.pos = (self.ids.fish.center_x + random.randint(-dp(50), dp(50)),
                             self.ids.fish.center_y + random.randint(-dp(50), dp(50)))
                bubble.velocity_x = random.uniform(-2, 2)
                bubble.velocity_y = random.uniform(1, 4)
                bubble.lifetime = random.uniform(3, 6)
                bubble.width = dp(random.randint(4, 8))
                bubble.height = dp(random.randint(4, 8))
                self.deep_container.add_widget(bubble)
                self.deep_particles.append(bubble)
        self.ids.level_complete.opacity = 1

    def go_home(self):
        # Smooth slide transition back to menu
        self.manager.transition = SlideTransition(direction='right', duration=0.5)
        self.manager.current = "menu"
    
    def go_settings(self):
        # Smooth slide transition to settings
        self.manager.transition = SlideTransition(direction='up', duration=0.4)
        self.manager.current = "settings"


class ClickerApp(App):
    LEVEL = 0

    FISHES = {
        'fish1':
            {'source': 'assets/fish1.png', 'hp': 10},
        'fish2':
            {'source': 'assets/fish2.png', 'hp': 20},
        'fish3':
            {'source': 'assets/fish3.png', 'hp': 30},
        'fish4':
            {'source': 'assets/fish4.png', 'hp': 40},
        'fish5':
            {'source': 'assets/fish5.png', 'hp': 50}
    }

    LEVELS = [
        ['fish1', 'fish2', 'fish3', 'fish4', 'fish5']
    ]

    def build(self):
        # Set the window icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'Clicker.png')
            if os.path.exists(icon_path):
                Window.set_icon(icon_path)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))

        return sm


if platform != 'android':
    Window.size = (450, 900)

if __name__ == '__main__':
    app = ClickerApp()
    app.run()
