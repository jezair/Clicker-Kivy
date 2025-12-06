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


class Menu(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

    # Перехід до екрана гри
    def go_game(self, *args):
        self.manager.current = "game"
        self.manager.transition.direction = "left"

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


# Клас для обертання картинок; в класі, який спадковує потрібно дадати властивість angle
class RotatedImage(Image):
    ...


# --------------------
# КЛАС МІНИ
# --------------------
class Mine(RotatedImage):
    anim_play = False
    interaction_block = True
    COEF_MULT = 1.5
    mine_current = None
    mine_index = 0
    hp_current = None
    angle = NumericProperty(0)

    def on_kv_post(self, base_widget):
        # посилання на екран гри
        try:
            self.GAME_SCREEN = self.parent.parent  # зазвичай буде додано прямо в Game
        except Exception:
            self.GAME_SCREEN = None
        return super().on_kv_post(base_widget)

    def new_mine(self, near_widget):
        """
        Розмістити міну поряд з given widget (наприклад рибою).
        """
        # Встановлюємо зображення для міни
        self.source = app.MINE_SOURCE if hasattr(app, "MINE_SOURCE") else "assets/images/mine.png"
        # Підібрати розмір (залежно від риби)
        try:
            self.size = (near_widget.width * 0.5, near_widget.height * 0.5)
        except Exception:
            self.size = (50, 50)

        # Розміщуємо поряд (праворуч і трохи нижче) - якщо не влізло, підлаштовуємо
        x = near_widget.x + near_widget.width + 10
        y = near_widget.y + (near_widget.height - self.height) / 2
        # Якщо виходить за межі екрану, поставимо ліворуч
        if hasattr(self, "GAME_SCREEN") and self.GAME_SCREEN:
            if x + self.width > self.GAME_SCREEN.width:
                x = near_widget.x - self.width - 10
        self.pos = (x, y)
        self.opacity = 1
        self.interaction_block = False

        # Легка анімація "пульсації" щоб було видно міну
        pulse = Animation(scale=1.05, duration=0.6) + Animation(scale=1.0, duration=0.6)
        # не всі Image мають scale — використаємо зміни розміру як імітацію
        pulse &= Animation(size=(self.size[0] * 1.05, self.size[1] * 1.05), duration=0.6) + Animation(size=self.size, duration=0.6)
        pulse.repeat = True
        # Запускаємо анімацію, зберігаємо посилання для зупинки пізніше
        self._pulse_anim = pulse
        pulse.start(self)

    def explode_and_remove(self):
        # відключаємо подальшу взаємодію
        self.interaction_block = True
        self.anim_play = True

        # Анімація вибуху — збільшення + зникнення
        old_size = self.size.copy()
        new_size = (self.size[0] * 2.5, self.size[1] * 2.5)
        anim = Animation(size=new_size, duration=0.25, t='out_cubic') + Animation(opacity=0, duration=0.25)
        anim.start(self)
        # після завершення — видалити віджет
        anim.bind(on_complete=lambda *a: (self._stop_and_remove(), None))

    def _stop_and_remove(self):
        # зупинити будь-які анімації
        try:
            if hasattr(self, "_pulse_anim"):
                self._pulse_anim.cancel(self)
        except Exception:
            pass
        # безпечно зняти з батька
        if self.parent:
            try:
                self.parent.remove_widget(self)
            except Exception:
                pass

    # Клік по міні
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return

        # Натиснули на міну
        # Знімаємо 2 очка (але не нижче 0)
        try:
            if hasattr(self, "GAME_SCREEN") and self.GAME_SCREEN:
                new_score = max(0, self.GAME_SCREEN.score - 2)
                self.GAME_SCREEN.score = new_score
            else:
                # на випадок, якщо посилання не встановлене, намагаємось через App
                app_root = App.get_running_app()
                if hasattr(app_root, "root") and hasattr(app_root.root, "get_screen"):
                    try:
                        game_screen = app_root.root.get_screen("game")
                        game_screen.score = max(0, game_screen.score - 2)
                    except Exception:
                        pass
        except Exception:
            pass

        # Запускаємо "вибух" та видалення
        self.explode_and_remove()

        return super().on_touch_down(touch)


# --------------------
# КЛАС РИБИ: Обробка кліків, створення "нової" риби
# --------------------
class Fish(RotatedImage):
    # Властивість для забезпечення програвання однієї анімації в один проміжок часу
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

        # Створюємо міну поруч з рибою трохи після старту руху (щоб риба була видима)
        # Додаємо міну як дитину екрану гри
        def create_mine(dt):
            mine = Mine()
            # Додаємо в ієрархію — зазвичай GAME_SCREEN є контейнером
            try:
                # переконаємось що minimum image доступне (app.MINE_SOURCE)
                if not hasattr(app, "MINE_SOURCE"):
                    app.MINE_SOURCE = "assets/images/mine.png"
                self.GAME_SCREEN.add_widget(mine)
                # гарантуємо, що mine.GAME_SCREEN вказано
                mine.GAME_SCREEN = self.GAME_SCREEN
                mine.new_mine(self)
            except Exception:
                pass

        Clock.schedule_once(create_mine, 0.9)

    # Перемогли рибу : )
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

        anim &= Animation(opacity=0)
        anim.start(self)

    # КЛІК!
    def on_touch_down(self, touch):
        # Клік не обробляється, якщо не потрпаляє в рибу
        # або анімація зараз програється або заблокована взаємодія
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return

        if not self.anim_play and not self.interaction_block:
            self.hp_current -= 1
            self.GAME_SCREEN.score += 1

            # Клік призвів до змеьшення hp риби
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
        # При завершенні рівня — прибрати усі міни зі сцени
        try:
            to_remove = [w for w in self.children[:] if isinstance(w, Mine)]
            for m in to_remove:
                try:
                    m._stop_and_remove()
                except Exception:
                    if m.parent:
                        m.parent.remove_widget(m)
        except Exception:
            pass

    def go_home(self):
        self.manager.current = "menu"
        self.manager.transition.direction = "right"


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

    # ДОДАВ: ресурс міни
    MINE_SOURCE = 'assets/images/mine.png'

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
