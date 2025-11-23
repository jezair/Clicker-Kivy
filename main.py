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
from random import randint


class Menu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    # Перехід до екрана гри
    def go_game(self, *args):
        game_screen = self.manager.get_screen("game")
        game_screen.hardmodee = False
        self.manager.current = "game"
        self.manager.transition.direction = "left"

    def go_hardmode(self, *args):
        game_screen = self.manager.get_screen("game")
        game_screen.hardmodee = True
        self.manager.current = "game"
        self.manager.transition.direction = "right"

    def updatelabels(self):
        game_screen = self.manager.get_screen("game")
        game_screen.ids.hp_label.opacity = 1 if game_screen.hardmodee else 0
        game_screen.ids.fish_label.opacity = 1 if game_screen.hardmodee else 0
        game_screen.ids.dismiss_fish_button.opacity = 1 if game_screen.hardmodee else 0
        game_screen.ids.buy_curtains_button.opacity = 1 if game_screen.hardmodee else 0
        game_screen.ids.curtainone.opacity = 1 if game_screen.hardmodee and game_screen.Curtains_current >= 1 else 0
        game_screen.ids.curtaintwo.opacity = 1 if game_screen.hardmodee and game_screen.Curtains_current >= 2 else 0
        game_screen.ids.curtainthree.opacity = 1 if game_screen.hardmodee and game_screen.Curtains_current >= 3 else 0
        game_screen.ids.curtainfour.opacity = 1 if game_screen.hardmodee and game_screen.Curtains_current >= 4 else 0

    # Перехід до екрана налаштувань
    def go_settings(self, *args):
        self.manager.current = "settings"
        self.manager.transition.direction = "up"

    # Вихід з програми
    def exit_app(self, *args):
        app.stop()


class Settings(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Повернення до меню
    def go_menu(self, *args):
        self.manager.current = "menu"
        self.manager.transition.direction = "down"

class Shop(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Повернення до меню
    def go_game(self, *args):
        self.manager.current = "game"
        self.manager.transition.direction = "up"


# Клас для обертання картинок; в класі, який спадковує потрібно дадати властивість angle
class RotatedImage(Image):
    ...


class Curtains(RotatedImage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.usede = False
    angle = NumericProperty(0)

    def Use(self, *args):
        game_screen = self.parent.parent.parent
        game_screen.Curtains_current -= 1
        game_screen.ids.fish.findfish()
        self.opacity = 0
        self.usede = True
    
    def on_touch_down(self, touch):
        game_screen = self.parent.parent.parent
        if game_screen.ids.fish.hidden_fishe and not self.usede and self.collide_point(*touch.pos) and game_screen.hardmodee:
            self.Use()
        return super().on_touch_down(touch)

# КЛАС РИБИ: Обробка кліків, створення "нової" риби
class Fish(RotatedImage):
    # Властивість для забезпечення програвання однієї анімації в один проміжок часу
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.whitch_fishe = None #0 нормальна рибка, 1 зла рибка.
        self.hidden_fishe = None
        self.anim_play = False
        self.interaction_block = True
        self.COEF_MULT = 1.5
        self.fish_current = None
        self.fish_index = 0
        self.hp_current = None
    angle = NumericProperty(0)

    def on_kv_post(self, base_widget):
        self.GAME_SCREEN = self.parent.parent.parent

        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        game_screen = self.parent.parent.parent
        if game_screen.hid_fish_count >= 2:
            game_screen.hid_fish_restrict = 3
        if game_screen.hardmodee:
            self.whitch_fishe = randint(0,1)
            self.hidden_fishe =  bool(randint(0,1))
            if self.hidden_fishe and game_screen.hid_fish_restrict == 0:
                game_screen.hid_fish_count += 1
            else:
                game_screen.hid_fish_count = 0
            if game_screen.hid_fish_restrict > 0:
                self.hidden_fishe = False
                game_screen.hid_fish_restrict -= 1
            if not self.hidden_fishe:
                self.source = 'assets/images/fish_02.png' if randint(0,1) == 1 else 'assets/images/fish_01.png'
            else:
                self.source = 'assets/images/fish_hidden.png'
            self.hp_current = randint(10,30)
            if not self.hidden_fishe:
                game_screen.ids.fish_label.text = "Angry fish" if self.whitch_fishe == 1 else "Normal fish"
            else:
                game_screen.ids.fish_label.text = "The fish hid!"
        else:
            self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
            self.source = app.FISHES[self.fish_current]['source']
            self.hp_current = app.FISHES[self.fish_current]['hp']


        self.swim()

    def findfish(self, *args):
        game_screen = self.parent.parent.parent
        if self.hidden_fishe:
            self.hidden_fishe =  0
            if not self.hidden_fishe:
                self.source = 'assets/images/fish_02.png' if randint(0,1) == 1 else 'assets/images/fish_01.png'
            else:
                self.source = 'assets/images/fish_hidden.png'
            if not self.hidden_fishe:
                game_screen.ids.fish_label.text = "Angry fish" if self.whitch_fishe == 1 else "Normal fish"
            else:
                game_screen.ids.fish_label.text = "The fish hid!"


    def swim(self):
        self.pos = (self.GAME_SCREEN.x - self.width, self.GAME_SCREEN.height / 2)
        self.opacity = 1
        swim = Animation(x=self.GAME_SCREEN.width / 2 - self.width / 2, duration=1)
        swim.start(self)

        swim.bind(on_complete=lambda w, a: setattr(self, "interaction_block", False))

    # Перемогли рибу :)
    def defeated(self):
        self.interaction_block = True
        # Анімація обертання
        anim = Animation(angle=self.angle + 360, d=1, t='in_cubic')

        # Запам'ятовуємо старі розмір і позицію для анімації зменьшення
        old_size = self.size.copy()
        old_pos = self.pos.copy()
        # Новий розмір
        new_size = (self.size[0] * self.COEF_MULT * 3, self.size[1] * self.COEF_MULT * 3)
        # Нова позиція риби при збільшенні
        new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2, self.pos[1] - (new_size[0] - self.size[1]) / 2)
        # АНІМАЦІЯ ЗБІЛЬШЕННЯ/ЗМЕНЬШЕННЯ
        anim &= Animation(size=(new_size), t='in_out_bounce') + Animation(size=(old_size), duration=0)
        anim &= Animation(pos=(new_pos), t='in_out_bounce') + Animation(pos=(old_pos), duration=0)

        # anim = Animation(size=(self.size[0] * self.COEF_MULT * 2, self.size[1] * self.COEF_MULT * 2)) + Animation(size=old_size)
        anim &= Animation(opacity=0)  # + Animation(opacity = 1)
        anim.start(self)

    # КЛІК!
    def on_touch_down(self, touch):
        # Клік не обробляється, якщо не потрпаляє в рибу 
        # або анімація зараз програється або заблокована взаємодія
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return

        if not self.anim_play and not self.interaction_block:
            game_screen = self.parent.parent.parent
            if game_screen.hardmodee and self.whitch_fishe == 1:
                game_screen.hp -= 2
            else:
                self.hp_current -= 1
                self.GAME_SCREEN.score += 1

            # Клік призвів до зменьшення hp риби
            if self.hp_current > 0:
                # Запам'ятовуємо старі розмір і позицію для анімації зменьшення
                old_size = self.size.copy()
                old_pos = self.pos.copy()

                # Новий розмір
                new_size = (self.size[0] * self.COEF_MULT, self.size[1] * self.COEF_MULT)
                # Нова позиція риби при збільшенні
                new_pos = (self.pos[0] - (new_size[0] - self.size[0]) / 2,
                           self.pos[1] - (new_size[0] - self.size[1]) / 2)

                # АНІМАЦІЯ ЗБІЛЬШЕННЯ/ЗМЕНЬШЕННЯ
                zoom_anim = Animation(size=(new_size), duration=0.05) + Animation(size=(old_size), duration=0.05)
                zoom_anim &= Animation(pos=(new_pos), duration=0.05) + Animation(pos=(old_pos), duration=0.05)

                zoom_anim.start(self)
                self.anim_play = True

                zoom_anim.bind(on_complete=lambda *args: setattr(self, "anim_play", False))
            # Клік призвів до знищення риби
            else:
                self.defeated()

                # Запуск нової риби або анімації завершення рівня після 1 секунди програвання зникнення риби
                if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1 or game_screen.hardmodee:
                    self.fish_index += 1
                    Clock.schedule_once(self.new_fish, 1.2)
                else:
                    Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)
                
                if game_screen.hardmodee and self.GAME_SCREEN.hp <= 0:
                    Clock.schedule_once(self.GAME_SCREEN.lose_game, 1.2)


        return super().on_touch_down(touch)

class Game(Screen):
    shope = False
    score = NumericProperty(0)
    hp = NumericProperty(25)
    hardmodee = False
    hid_fish_count = 0
    hid_fish_restrict = 0
    Curtains_current = NumericProperty(2)
    Curtains_max = NumericProperty(4)
    

    def on_pre_enter(self, *args):
        if not self.shope:
            self.score = 0
            app.LEVEL = 0
            self.ids.level_complete.opacity = 0
            self.hid_fish_count = 0
            self.hid_fish_restrict = 0
            self.ids.fish.fish_index = 0
            self.Curtains_current = 2
            self.ids.lose_game.opacity = 0
            self.ids.curtainone.usede = False if self.hardmodee and self.Curtains_current >= 1 else True
            self.ids.curtaintwo.usede = False if self.hardmodee and self.Curtains_current >= 1 else True
            self.ids.curtainthree.usede = False if self.hardmodee and self.Curtains_current >= 1 else True
            self.ids.curtainfour.usede = False if self.hardmodee and self.Curtains_current >= 1 else True

        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()

        return super().on_enter(*args)

    def start_game(self):
        if not self.shope:
            self.ids.fish.new_fish()

    def level_complete(self, *args):
        # self.ids.level_complete.opacity = 1
        self.ids.level_complete.opacity = 1

    def lose_game(self, *args):
        self.ids.lose_game.opacity = 1

    def buy_curtain(self, much):
        if self.Curtains_current + much <= self.Curtains_max and self.score >= much * 75:
            self.Curtains_current += much
            self.score -= much * 75
            self.respowntaniouscombustion()

    def respowntaniouscombustion(self):
        self.ids.curtainone.opacity = 1 if self.hardmodee and self.Curtains_current >= 1 else 0
        self.ids.curtainone.usede = 0 if self.hardmodee and self.Curtains_current >= 1 else 1
        self.ids.curtaintwo.opacity = 1 if self.hardmodee and self.Curtains_current >= 2 else 0
        self.ids.curtaintwo.usede = 0 if self.hardmodee and self.Curtains_current >= 2 else 1
        self.ids.curtainthree.opacity = 1 if self.hardmodee and self.Curtains_current >= 3 else 0
        self.ids.curtainthree.usede = 0 if self.hardmodee and self.Curtains_current >= 3 else 1
        self.ids.curtainfour.opacity = 1 if self.hardmodee and self.Curtains_current >= 4 else 0
        self.ids.curtainfour.usede = 0 if self.hardmodee and self.Curtains_current >= 4 else 1

    def go_home(self):
        self.manager.current = "menu"
        if self.hardmodee:
            self.manager.transition.direction = "left"
        else:
            self.manager.transition.direction = "right"
        self.hp = 25
        self.shope = False

    def go_shop(self):
        self.manager.current = "shop"
        self.manager.transition.direction = "down"
        self.shope = True
    def dissmiss_fish(self):
        self.ids.fish.defeated()
        Clock.schedule_once(self.ids.fish.new_fish, 1.2)
        if self.hardmodee and self.hp <= 0:
            Clock.schedule_once(self.lose_game, 1.2)
class ClickerApp(App):
    LEVEL = 0

    FISHES = {
        'fish1':
            {'source': 'assets/images/fish_01.png', 'hp': 10},
        'fish2':
            {'source': 'assets/images/fish_02.png', 'hp': 20}
    }

    LEVELS = [
        ['fish1', 'fish1', 'fish2']
    ]

    def build(self):
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))
        sm.add_widget(Shop(name="shop"))

        return sm


if platform != 'android':
    Window.size = (450, 900)

app = ClickerApp()
app.run()