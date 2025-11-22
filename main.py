from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.utils import hex_colormap, colormap
from kivy.animation import Animation
from kivy.metrics import sp, dp
from kivy.uix.image import Image
from kivy import platform
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy.core.audio import SoundLoader   # <<< використовуємо SoundLoader
import os

class Menu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    def go_game(self, *args):
        self.manager.current = "game"
        self.manager.transition.direction = "left"

    def go_settings(self, *args):
        self.manager.current = "settings"
        self.manager.transition.direction = "up"

    def exit_app(self, *args):
        app_inst = App.get_running_app()
        if getattr(app_inst, "music", None):
            try:
                app_inst.music.stop()
                print("Music stopped.")
            except Exception as e:
                print("Error stopping music:", e)
        App.get_running_app().stop()


class Settings(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def go_menu(self, *args):
        self.manager.current = "menu"
        self.manager.transition.direction = "down"


class RotatedImage(Image):
    pass


class Fish(RotatedImage):
    anim_play = False
    interaction_block = True
    COEF_MULT = 1.5
    fish_current = None
    fish_index = 0
    hp_current = None
    angle = NumericProperty(0)

    def on_kv_post(self, base_widget):
        # Game screen — це два рівні вверх в ієрархії у твоєму kv
        self.GAME_SCREEN = self.parent.parent.parent
        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        self.fish_current = App.get_running_app().LEVELS[App.get_running_app().LEVEL][self.fish_index]
        self.source = App.get_running_app().FISHES[self.fish_current]['source']
        self.hp_current = App.get_running_app().FISHES[self.fish_current]['hp']
        self.swim()

    def swim(self):
        self.pos = (self.GAME_SCREEN.x - self.width, self.GAME_SCREEN.height / 2)
        self.opacity = 1
        swim = Animation(x=self.GAME_SCREEN.width / 2 - self.width / 2, duration=1)
        swim.start(self)
        swim.bind(on_complete=lambda w, a: setattr(self, "interaction_block", False))

    def defeated(self):
        self.interaction_block = True
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')

        old_size = self.size.copy()
        old_pos = self.pos.copy()

        new_size = (self.size[0] * self.COEF_MULT * 3, self.size[1] * self.COEF_MULT * 3)
        new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2,
                   self.pos[1] - (new_size[1] - self.size[1]) / 2)

        anim &= Animation(size=new_size, t='in_out_bounce') + Animation(size=old_size, duration=0)
        anim &= Animation(pos=new_pos, t='in_out_bounce') + Animation(pos=old_pos, duration=0)
        anim &= Animation(opacity=0)

        anim.start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return

        if not self.anim_play and not self.interaction_block:
            self.hp_current -= 1
            self.GAME_SCREEN.score += 1

            if self.hp_current > 0:
                old_size = self.size.copy()
                old_pos = self.pos.copy()

                new_size = (self.size[0] * self.COEF_MULT, self.size[1] * self.COEF_MULT)
                new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2,
                           self.pos[1] - (new_size[1] - self.size[1]) / 2)

                zoom_anim = Animation(size=new_size, duration=0.05) + Animation(size=old_size, duration=0.05)
                zoom_anim &= Animation(pos=new_pos, duration=0.05) + Animation(pos=old_pos, duration=0.05)

                zoom_anim.start(self)
                self.anim_play = True
                zoom_anim.bind(on_complete=lambda *args: setattr(self, "anim_play", False))

            else:
                self.defeated()

                if len(App.get_running_app().LEVELS[App.get_running_app().LEVEL]) > self.fish_index + 1:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)

        return super().on_touch_down(touch)


class Game(Screen):
    score = NumericProperty(0)

    def on_pre_enter(self, *args):
        self.score = 0
        App.get_running_app().LEVEL = 0
        # якщо id-ів немає в kv — це може викликати помилку, переконайся, що в твоєму kv є level_complete і fish
        try:
            self.ids.level_complete.opacity = 0
            self.ids.fish.fish_index = 0
        except Exception as e:
            print("Warning: ids not found in Game.on_pre_enter:", e)
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()
        return super().on_enter(*args)

    def start_game(self):
        try:
            self.ids.fish.new_fish()
        except Exception as e:
            print("Error starting game (ids.fish):", e)

    def level_complete(self, *args):
        try:
            self.ids.level_complete.opacity = 1
        except Exception:
            pass

    def go_home(self):
        self.manager.current = "menu"
        self.manager.transition.direction = "right"


class ClickerApp(App):
    LEVEL = 0
    music = None

    FISHES = {
        'fish1': {'source': 'assets/images/fish_01.png', 'hp': 10},
        'fish2': {'source': 'assets/images/fish_02.png', 'hp': 20}
    }

    LEVELS = [
        ['fish1', 'fish1', 'fish2']
    ]

    def build(self):
        # Шляхи, які будемо пробувати
        base_paths = [
            'assets/audios/music.mp3',  # твій mp3
            'assets/audios/music.ogg',  # спроба ogg
            'assets/audios/music.wav'   # спроба wav
        ]

        # Перевіримо відносні/абсолютні шляхи та наявність файлу
        found = False
        for p in base_paths:
            if os.path.exists(p):
                print("Found audio file:", p)
                self.music = SoundLoader.load(p)
                if self.music:
                    print("Music loaded:", p, " — length:", getattr(self.music, 'length', 'unknown'))
                    found = True
                    break
                else:
                    print("SoundLoader failed to load (provider issue?) for:", p)
            else:
                print("Audio file not found at:", p)

        if not found:
            print("No playable audio loaded. Convert your music to .ogg or .wav and place into assets/audios/")
        else:
            try:
                self.music.volume = 0.5
                # деякі провайдери не мають атрибута loop — перевіряємо
                if hasattr(self.music, "loop"):
                    self.music.loop = True
                # Спробуємо запустити
                status = self.music.play()
                print("Attempted to play music, play() returned:", status)
            except Exception as e:
                print("Error when trying to play music:", e)

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
