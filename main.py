from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import hex_colormap, colormap
from kivy.animation import Animation
from kivy.metrics import sp, dp
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy import platform
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import SlideTransition, FadeTransition, SwapTransition
import io
import os


class Menu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

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
    hp_current = None
    angle = NumericProperty(0)
    scale = NumericProperty(1.0)
    is_clicked = BooleanProperty(False)

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
        self.hp_current = app.FISHES[self.fish_current]['hp']

        self.swim()

    def swim(self):
        # Improved appearance animation
        self.pos = (-self.width, self.GAME_SCREEN.height / 2 - self.height / 2)
        self.opacity = 0
        self.scale = 0.5
        
        # Fade in and scale to normal size while sliding
        target_x = self.GAME_SCREEN.width / 2 - self.width / 2
        
        # Combine animations: slide, fade in, and scale up
        slide_anim = Animation(x=target_x, duration=0.8, t='out_quad')
        fade_anim = Animation(opacity=1, duration=0.5, t='linear')
        scale_anim = Animation(scale=1.0, duration=0.6, t='out_elastic')
        
        # Start all animations together
        swim = slide_anim & fade_anim & scale_anim
        swim.start(self)
        swim.bind(on_complete=lambda w, a: setattr(self, "interaction_block", False))

    # Перемогли рибу :)
    def defeated(self):
        self.interaction_block = True
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
        # Update score immediately
        if hasattr(self, 'GAME_SCREEN') and self.GAME_SCREEN:
            self.GAME_SCREEN.score += 1
        
        if self.hp_current <= 0:
            # Simple defeat - just fade out
            self.defeated()
            # Wait for defeat animation then spawn next fish
            Clock.schedule_once(self._spawn_next_fish, 0.3)
        else:
            # Fish still alive - reset for next click
            self.anim_play = False
            self.interaction_block = False
    
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

    def on_pre_enter(self, *args):
        self.score = 0
        app.LEVEL = 0
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0

        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()
        self.load_gif_background()
        # Bind window resize to update GIF size
        Window.bind(on_resize=self.on_window_resize)
        return super().on_enter(*args)

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

    def level_complete(self, *args):
        # self.ids.level_complete.opacity = 1
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

app = ClickerApp()
app.run()
