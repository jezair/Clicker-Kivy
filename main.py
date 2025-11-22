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
import random
import math


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
        app.stop()


class Settings(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def go_menu(self, *args):
        self.manager.current = "menu"
        self.manager.transition.direction = "down"


class RotatedImage(Image):
    ...


class Fish(RotatedImage):
    direction = 1
    move_speed = 3
    wave_time = 0
    anim_play = False
    interaction_block = True
    COEF_MULT = 1.5
    fish_current = None
    fish_index = 0
    hp_current = None
    angle = NumericProperty(0)

    def on_kv_post(self, base_widget):
        self.GAME_SCREEN = self.parent.parent.parent
        return super().on_kv_post(base_widget)

    def stop_all_movement(self):
        Animation.cancel_all(self)
        Clock.unschedule(self.update_fish_movement)

    def new_fish(self, *args):
        self.stop_all_movement()

        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]['source']
        self.hp_current = app.FISHES[self.fish_current]['hp']

        self.wave_time = 0

        self.swim()

    def swim(self):
        self.opacity = 1
        self.interaction_block = False

        # ставим рыбу строго в центре (не выходит за края)
        self.x = (self.GAME_SCREEN.width - self.width) / 2
        self.y = (self.GAME_SCREEN.height - self.height) / 2

        Clock.schedule_interval(self.update_fish_movement, 1 / 60)

        self.start_random_movement()

    # ============= ОБНОВЛЁННОЕ ДВИЖЕНИЕ — строго внутри экрана =============
    def start_random_movement(self, *args):
        if self.interaction_block:
            return

        # рыба дотрагивается до краёв, НО НЕ ВЫХОДИТ ЗА НИХ
        min_x = 0
        max_x = self.GAME_SCREEN.width - self.width

        min_y = 0
        max_y = self.GAME_SCREEN.height - self.height

        # выбираем точку ТОЛЬКО в реальной зоне, без воздуха
        new_x = random.randint(int(min_x), int(max_x))
        new_y = random.randint(int(min_y), int(max_y))

        distance = ((new_x - self.x) ** 2 + (new_y - self.y) ** 2) ** 0.5
        duration = distance / 150

        anim = Animation(x=new_x, y=new_y, duration=duration, t='linear')
        anim.bind(on_complete=self.start_random_movement)
        anim.start(self)

    # ============= ОГРАНИЧЕНИЕ ВОЛНЫ, чтоб не вылетала ======================
    def update_fish_movement(self, dt):
        if self.interaction_block:
            return

        self.wave_time += dt * 4
        self.y += math.sin(self.wave_time) * 8

        # ограничение ровно по краям
        self.y = max(0, min(self.y, self.GAME_SCREEN.height - self.height))

    # =======================================================================

    def defeated(self):
        self.interaction_block = True
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')

        old_size = self.size.copy()
        old_pos = self.pos.copy()
        new_size = (self.size[0] * self.COEF_MULT * 3, self.size[1] * self.COEF_MULT * 3)
        new_pos = (
            self.pos[0] - (new_size[0] - self.size[0]) / 2,
            self.pos[1] - (new_size[0] - self.size[1]) / 2
        )

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

                new_size = (
                    self.size[0] * self.COEF_MULT,
                    self.size[1] * self.COEF_MULT
                )
                new_pos = (
                    self.pos[0] - (new_size[0] - self.size[0]) / 2,
                    self.pos[1] - (new_size[0] - self.size[1]) / 2
                )

                zoom_anim = Animation(size=new_size, duration=0.05) + Animation(size=old_size, duration=0.05)
                zoom_anim &= Animation(pos=new_pos, duration=0.05) + Animation(pos=old_pos, duration=0.05)

                zoom_anim.start(self)
                self.anim_play = True
                zoom_anim.bind(on_complete=lambda *a: setattr(self, "anim_play", False))

            else:
                self.defeated()

                if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)

        return super().on_touch_down(touch)


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
        return super().on_enter(*args)

    def start_game(self):
        self.ids.fish.new_fish()

    def level_complete(self, *args):
        self.ids.level_complete.opacity = 1

    def go_home(self):
        self.manager.current = "menu"
        self.manager.transition.direction = "right"


class ClickerApp(App):
    LEVEL = 0

    FISHES = {
        'fish1': {'source': 'assets/images/fish_01.png', 'hp': 10},
        'fish2': {'source': 'assets/images/fish_02.png', 'hp': 20}
    }

    LEVELS = [
        ['fish1', 'fish1', 'fish2']
    ]

    def build(self):
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))
        return sm


if platform != 'android':
    Window.size = (450, 900)

app = ClickerApp()
app.run()
