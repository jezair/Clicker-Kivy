from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy import platform
from kivy.storage.jsonstore import JsonStore

# ---------- SCREENS ----------

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

    # Изменение громкости
    def on_volume_change(self, slider, value):
        app.volume = value
        app.save_settings()

    # Изменение языка
    def on_language_change(self, language_code):
        app.language = language_code
        app.save_settings()


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
        self.GAME_SCREEN = self.parent.parent.parent
        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]['source']
        self.hp_current = app.FISHES[self.fish_current]['hp']
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
                   self.pos[1] - (new_size[0] - self.size[1]) / 2)

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
                           self.pos[1] - (new_size[0] - self.size[1]) / 2)

                zoom_anim = Animation(size=new_size, duration=0.05) + Animation(size=old_size, duration=0.05)
                zoom_anim &= Animation(pos=new_pos, duration=0.05) + Animation(pos=old_pos, duration=0.05)
                zoom_anim.start(self)
                self.anim_play = True
                zoom_anim.bind(on_complete=lambda *args: setattr(self, "anim_play", False))

            else:
                self.defeated()
                app.save_game()  # сохраняем после победы над рыбой

                if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)

        return super().on_touch_down(touch)


class Game(Screen):
    score = NumericProperty(0)

    def on_pre_enter(self, *args):
        if app.store.exists("progress"):
            data = app.store.get("progress")
            self.score = data["score"]
            self.ids.fish.fish_index = data["fish_index"]
        else:
            self.score = 0
            self.ids.fish.fish_index = 0
        self.ids.level_complete.opacity = 0
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()
        return super().on_enter(*args)

    def start_game(self):
        self.ids.fish.new_fish()

    def level_complete(self, *args):
        self.ids.level_complete.opacity = 1
        app.save_game()  # сохраняем прогресс после завершения уровня

    def go_home(self):
        self.manager.current = "menu"
        self.manager.transition.direction = "right"


# ---------- APP ----------

class ClickerApp(App):
    LEVEL = 0
    volume = 1.0
    language = "en"
    store = JsonStore("save.json")
    AUTOSAVE_INTERVAL = 5  # каждые 5 секунд

    FISHES = {
        'fish1': {'source': 'assets/images/fish_01.png', 'hp': 10},
        'fish2': {'source': 'assets/images/fish_02.png', 'hp': 20}
    }

    LEVELS = [
        ['fish1', 'fish1', 'fish2']
    ]

    def build(self):
        self.load_settings()
        self.load_game()

        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))

        Clock.schedule_interval(lambda dt: self.save_game(), self.AUTOSAVE_INTERVAL)

        return sm

    # ---------- SAVE/LOAD PROGRESS ----------
    def save_game(self):
        try:
            fish = self.root.get_screen("game").ids.fish
            game = self.root.get_screen("game")
            self.store.put("progress",
                           level=self.LEVEL,
                           fish_index=fish.fish_index,
                           score=game.score)
        except:
            pass

    def load_game(self):
        if self.store.exists("progress"):
            data = self.store.get("progress")
            self.LEVEL = data["level"]

    # ---------- SAVE/LOAD SETTINGS ----------
    def save_settings(self):
        self.store.put("settings",
                       volume=self.volume,
                       language=self.language)

    def load_settings(self):
        if self.store.exists("settings"):
            data = self.store.get("settings")
            self.volume = data.get("volume", 1.0)
            self.language = data.get("language", "en")

    def on_stop(self):
        self.save_game()
        self.save_settings()


# ---------- RUN ----------

if platform != 'android':
    Window.size = (450, 900)

app = ClickerApp()
app.run()
