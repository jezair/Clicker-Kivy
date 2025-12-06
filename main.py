from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.clock import Clock
from kivy import platform
import random
import math


class Menu(Screen):
    def go_game(self, *args):
        self.manager.current = "game"
        self.manager.transition.direction = "left"

    def go_settings(self, *args):
        self.manager.current = "settings"
        self.manager.transition.direction = "up"

    def exit_app(self, *args):
        app.stop()


class Settings(Screen):
    def go_menu(self, *args):
        self.manager.current = "menu"
        self.manager.transition.direction = "down"


class RotatedImage(Image):
    ...


# -----------------------------------------------------------
#                       МИНА
# -----------------------------------------------------------
class Mine(RotatedImage):
    angle = NumericProperty(0)
    wave_time = 0
    anim_play = False
    interaction_block = True

    def on_kv_post(self, base_widget):
        try:
            self.GAME_SCREEN = self.parent.parent  # Game screen
        except:
            self.GAME_SCREEN = None
        return super().on_kv_post(base_widget)

    def new_mine(self, near):
        self.source = "assets/images/mine.png"
        self.opacity = 1
        self.interaction_block = False

        # размер относительно рыбы
        self.size = (near.width * 0.45, near.height * 0.45)

        x = near.x + near.width + 20
        if x + self.width > self.GAME_SCREEN.width:
            x = near.x - self.width - 20

        y = near.y + (near.height - self.height) / 2
        self.pos = (x, y)

        # движение + волна
        Clock.schedule_interval(self.update_wave, 1/60)
        self.start_random_move()

    def start_random_move(self, *args):
        if self.interaction_block:
            return

        min_x = 0
        max_x = self.GAME_SCREEN.width - self.width
        min_y = 0
        max_y = self.GAME_SCREEN.height - self.height

        nx = random.randint(int(min_x), int(max_x))

        ny = random.randint(int(min_x), int(max_x))


        dist = math.hypot(nx - self.x, ny - self.y)
        duration = dist / 150

        anim = Animation(x=nx, y=ny, duration=duration, t="linear")
        anim.bind(on_complete=self.start_random_move)
        anim.start(self)

    def update_wave(self, dt):
        if self.interaction_block:
            return
        self.wave_time += dt * 4
        self.y += math.sin(self.wave_time) * 6
        self.y = max(0, min(self.y, self.GAME_SCREEN.height - self.height))

    def explode(self):
        self.interaction_block = True
        big = (self.width * 2.5, self.height * 2.5)
        anim = Animation(size=big, duration=0.25) + Animation(opacity=0, duration=0.25)
        anim.bind(on_complete=lambda *a: self.remove())
        anim.start(self)

    def remove(self):
        try:
            Clock.unschedule(self.update_wave)
            Animation.cancel_all(self)
        except:
            pass
        if self.parent:
            self.parent.remove_widget(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if self.interaction_block:
            return super().on_touch_down(touch)

        # -2 очка
        self.GAME_SCREEN.score = max(0, self.GAME_SCREEN.score - 2)
        self.explode()
        return True


# -----------------------------------------------------------
#                       РЫБА
# -----------------------------------------------------------
class Fish(RotatedImage):
    angle = NumericProperty(0)
    wave_time = 0
    anim_play = False
    interaction_block = True

    fish_index = 0
    hp_current = 0
    COEF_MULT = 1.5

    def on_kv_post(self, base_widget):
        self.GAME_SCREEN = self.parent.parent.parent
        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]['source']
        self.hp_current = app.FISHES[self.fish_current]['hp']

        self.wave_time = 0
        self.swim()

    def swim(self):
        self.opacity = 1
        self.interaction_block = False

        self.x = (self.GAME_SCREEN.width - self.width) / 2
        self.y = (self.GAME_SCREEN.height - self.height) / 2

        Clock.schedule_interval(self.update_wave, 1 / 60)
        self.start_random_move()

        # → Спавним мину чуть позже
        Clock.schedule_once(self.spawn_mine, 0.6)

    def spawn_mine(self, dt):
        mine = Mine()
        self.GAME_SCREEN.add_widget(mine)
        mine.GAME_SCREEN = self.GAME_SCREEN
        mine.new_mine(self)

    def start_random_move(self, *args):
        if self.interaction_block:
            return

        min_x = 0
        max_x = self.GAME_SCREEN.width - self.width + 100
        min_y = 0
        max_y = self.GAME_SCREEN.height - self.height - 100

        nx = random.randint(int(min_x), int(max_x))

        ny = random.randint(int(min_x), int(max_x))


        dist = math.hypot(nx - self.x, ny - self.y)
        duration = dist / 150

        anim = Animation(x=nx, y=ny, duration=duration, t="linear")
        anim.bind(on_complete=self.start_random_move)
        anim.start(self)

    def update_wave(self, dt):
        if self.interaction_block:
            return

        self.wave_time += dt * 4
        self.y += math.sin(self.wave_time) * 8
        self.y = max(0, min(self.y, self.GAME_SCREEN.height - self.height))

    def defeated(self):
        self.interaction_block = True
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')

        old_size = self.size.copy()
        old_pos = self.pos.copy()
        new_size = (old_size[0] * 3, old_size[1] * 3)
        new_pos = (
            old_pos[0] - (new_size[0] - old_size[0]) / 2,
            old_pos[1] - (new_size[1] - old_size[1]) / 2
        )

        anim &= Animation(size=new_size, t='in_out_bounce') + Animation(size=old_size, duration=0)
        anim &= Animation(pos=new_pos, t='in_out_bounce') + Animation(pos=old_pos, duration=0)
        anim &= Animation(opacity=0)
        anim.start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return

        self.hp_current -= 1
        self.GAME_SCREEN.score += 1

        if self.hp_current > 0:
            old_size = self.size.copy()
            old_pos = self.pos.copy()
            new_size = (old_size[0] * self.COEF_MULT, old_size[1] * self.COEF_MULT)
            new_pos = (
                old_pos[0] - (new_size[0] - old_size[0]) / 2,
                old_pos[1] - (new_size[1] - old_size[1]) / 2
            )

            zoom = Animation(size=new_size, duration=0.05) + Animation(size=old_size, duration=0.05)
            zoom &= Animation(pos=new_pos, duration=0.05) + Animation(pos=old_pos, duration=0.05)

            zoom.start(self)
            self.anim_play = True
            zoom.bind(on_complete=lambda *a: setattr(self, "anim_play", False))

        else:
            self.defeated()

            # следующая рыба или конец уровня
            if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                self.fish_index += 1
                Clock.schedule_once(self.new_fish, 1.2)
            else:
                Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)

        return super().on_touch_down(touch)


# -----------------------------------------------------------
#                       СЦЕНА ИГРЫ
# -----------------------------------------------------------
class Game(Screen):
    score = NumericProperty(0)

    def on_pre_enter(self, *args):
        self.score = 0
        app.LEVEL = 0
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.ids.fish.new_fish()
        return super().on_enter(*args)

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
