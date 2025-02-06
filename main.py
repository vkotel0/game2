from collections import OrderedDict
import random
from enum import property
from multiprocessing.dummy import list
from os import name
from threading import enumerate

from pygame import Rect
import pygame
import numpy as np
from pygame.examples.go_over_there import screen

WINDOW_WIDTH, WINDOW_HEIGHT = 500, 601
GRID_WIDTH, GRID_HEIGHT = 300, 600
TILE_SIZE = 30


def remove_empty_columns(arr, _x_offset=0, _keep_counting=True):
    for colid, col in enumerate(arr.T):
        if col.max() == 0:
            if _keep_counting:
                _x_offset += 1
            # Удаляем текущий столбец и пробуем снова.
            arr, _x_offset = remove_empty_columns(
                np.delete(arr, colid, 1), _x_offset, _keep_counting)
            break
        else:
            _keep_counting = False
    return arr, _x_offset


class Exception:
    pass


class BottomReached(Exception):
    pass


class TopReached(Exception):
    pass


class Block(pygame.sprite.Sprite):

    @staticmethod
    def collide(block, group):
        for other_block in group:
            # Игнорируем текущий блок, который всегда будет сталкиваться с самим собой.
            if block == other_block:
                continue
            if pygame.sprite.collide_mask(block, other_block) is not None:
                return True
        return False

    def init(self):
        super().init()
        # Получаем случайный цвет.
        self.color = random.choice((
            (200, 200, 200),
            (215, 133, 133),
            (30, 145, 255),
            (0, 170, 0),
            (180, 0, 140),
            (200, 200, 0)
        ))
        self.current = True
        self.struct = np.array(self.struct)
        # Начальная случайная ротация и отражение.
        if random.randint(0, 1):
            self.struct = np.rot90(self.struct)
        if random.randint(0, 1):
            # Отразить по оси X.
            self.struct = np.flip(self.struct, 0)
        self._draw()

    def _draw(self, x=4, y=0):
        width = len(self.struct[0]) * TILE_SIZE
        height = len(self.struct) * TILE_SIZE
        self.image = pygame.surface.Surface([width, height])
        self.image.set_colorkey((0, 0, 0))
        # Позиция и размер
        self.rect = Rect(0, 0, width, height)
        self.x = x
        self.y = y
        for y, row in enumerate(self.struct):
            for x, col in enumerate(row):
                if col:
                    pygame.draw.rect(
                        self.image,
                        self.color,
                        Rect(x * TILE_SIZE + 1, y * TILE_SIZE + 1,
                             TILE_SIZE - 2, TILE_SIZE - 2)
                    )
        self._create_mask()

    def redraw(self):
        self._draw(self.x, self.y)

    def _create_mask(self):
        self.mask = pygame.mask.from_surface(self.image)

    def initial_draw(self):
        raise NotImplementedError

    @property
    def group(self):
        return self.groups()[0]

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.rect.left = value * TILE_SIZE

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.rect.top = value * TILE_SIZE

    def move_left(self, group):
        self.x -= 1
        # Проверяем, достигли ли мы левой границы.
        if self.x < 0 or Block.collide(self, group):
            self.x += 1

    def move_right(self, group):
        self.x += 1
        # Проверяем, достигли ли мы правой границы или столкнулись с другим
        # блоком.
        if self.rect.right > GRID_WIDTH or Block.collide(self, group):
            # Откат.
            self.x -= 1

    def move_down(self, group):
        self.y += 1
        # Проверяем, достиг ли блок низа или столкнулся с
        # другим.
        if self.rect.bottom > GRID_HEIGHT or Block.collide(self, group):
            # Откат к предыдущей позиции.
            self.y -= 1
            self.current = False
            raise BottomReached


def rotate(self, group):
    self.image = pygame.transform.rotate(self.image, 90)
    # После поворота нужно обновить размер и позицию.
    self.rect.width = self.image.get_width()
    self.rect.height = self.image.get_height()
    self._create_mask()
    # Проверяем, не выходит ли новая позиция за пределы или не сталкивается
    # с другими блоками, и корректируем ее при необходимости.
    while self.rect.right > GRID_WIDTH:
        self.x -= 1
    while self.rect.left < 0:
        self.x += 1
    while self.rect.bottom > GRID_HEIGHT:
        self.y -= 1
    while True:
        if not Block.collide(self, group):
            break
        self.y -= 1
    self.struct = np.rot90(self.struct)


def update(self):
    if self.current:
        self.move_down()


class SquareBlock(Block):
    struct = (
        (1, 1),
        (1, 1)
    )


class TBlock(Block):
    struct = (
        (1, 1, 1),
        (0, 1, 0)
    )


class LineBlock(Block):
    struct = (
        (1,),
        (1,),
        (1,),
        (1,)
    )


class LBlock(Block):
    struct = (
        (1, 1),
        (1, 0),
        (1, 0),
    )


class ZBlock(Block):
    struct = (
        (0, 1),
        (1, 1),
        (1, 0),
    )


def super():
    pass


def staticmethod(args):
    pass


class BlocksGroup(pygame.sprite.OrderedUpdates):

    @staticmethod
    def get_random_block():
        return random.choice(
            (SquareBlock, TBlock, LineBlock, LBlock, ZBlock))()

    def init(self, *args, **kwargs):
        super().init(self, *args, **kwargs)
        self._reset_grid()
        self._ignore_next_stop = False
        self.score = 0
        self.next_block = None
        # Не движется, просто для инициализации атрибута.
        self.stop_moving_current_block()
        # Первый блок.
        self._create_new_block()

    def _check_line_completion(self):
        # Начинаем проверку снизу.
        for i, row in enumerate(self.grid[::-1]):
            if all(row):
                self.score += 5
                # Получаем блоки, затронутые удалением линии, и
                # удаляем дубликаты.
                affected_blocks = list(
                    OrderedDict.fromkeys(self.grid[-1 - i]))

                for block, y_offset in affected_blocks:
                    # Удаляем тайлы блока, которые принадлежат
                    # завершенной линии.
                    block.struct = np.delete(block.struct, y_offset, 0)
                    if block.struct.any():
                        # После удаления проверяем, есть ли пустые столбцы,
                        # так как их нужно опустить.
                        block.struct, x_offset = \
                            remove_empty_columns(block.struct)
                        # Компенсируем пространство, которое ушло со столбцами, чтобы
                        # сохранить оригинальную позицию блока.
                        block.x += x_offset
                        # Принудительное обновление.
                        block.redraw()
                    else:
                        # Если структура пустая, значит, блок исчез.
                        self.remove(block)

                # Вместо проверки, какие блоки нужно переместить
                # после завершения линии, просто попробуем переместить все.
                for block in self:
                    # Кроме текущего блока.
                    if block.current:
                        continue
                    # Опускаем каждый блок, пока он не достигнет
                    # низа или не столкнется с другим блоком.
                    while True:
                        try:
                            block.move_down(self)
                        except BottomReached:
                            break


                        self.update_grid()
# Поскольку мы обновили сетку, теперь счетчик i
# больше не является действительным, поэтому вызываем функцию снова
# чтобы проверить, есть ли другие завершенные линии в новой сетке.
                        self._check_line_completion()
                    break


def range(param):
    pass


def _reset_grid(self):
    self.grid = [[0 for _ in range(10)] for _ in range(20)]


def _create_new_block(self):
    new_block = self.next_block or BlocksGroup.get_random_block()
    if Block.collide(new_block, self):
        raise TopReached
    self.add(new_block)
    self.next_block = BlocksGroup.get_random_block()
    self.update_grid()
    self._check_line_completion()


def update_grid(self):
    self._reset_grid()
    for block in self:
        for y_offset, row in enumerate(block.struct):
            for x_offset, digit in enumerate(row):
                # Предотвращаем замену предыдущих блоков.
                if digit == 0:
                    continue
                rowid = block.y + y_offset
                colid = block.x + x_offset
                self.grid[rowid][colid] = (block, y_offset)


@property
def current_block(self):
    return self.sprites()[-1]


def update_current_block(self):
    try:
        self.current_block.move_down(self)
    except BottomReached:
        self.stop_moving_current_block()
        self._create_new_block()
    else:
        self.update_grid()


def move_current_block(self):
    # Сначала проверяем, есть ли что-то, что нужно переместить.
    if self._current_block_movement_heading is None:
        return
    action = {
        pygame.K_DOWN: self.current_block.move_down,
        pygame.K_LEFT: self.current_block.move_left,
        pygame.K_RIGHT: self.current_block.move_right,
    }
    try:
        # Каждая функция требует группу в качестве первого аргумента
        # для проверки возможного столкновения.
        action[self._current_block_movement_heading](self)
    except BottomReached:
        self.stop_moving_current_block()
        self._create_new_block()
    else:
        self.update_grid()


def start_moving_current_block(self, key):
    if self._current_block_movement_heading is not None:
        self._ignore_next_stop = True
    self._current_block_movement_heading = key


def stop_moving_current_block(self):
    if self._ignore_next_stop:
        self._ignore_next_stop = False
    else:
        self._current_block_movement_heading = None


def rotate_current_block(self):
    # Предотвращаем поворот SquareBlocks.
    if not isinstance(self.current_block, SquareBlock):
        self.current_block.rotate(self)
        self.update_grid()


def draw_grid(background):
    """Рисуем фоновую сетку."""
    grid_color = 50, 50, 50
    # Вертикальные линии.
    for i in range(11):
        x = TILE_SIZE * i
        pygame.draw.line(
            background, grid_color, (x, 0), (x, GRID_HEIGHT)
        )
    # Горизонтальные линии.
    for i in range(21):
        y = TILE_SIZE * i
        pygame.draw.line(
            background, grid_color, (0, y), (GRID_WIDTH, y)
        )


def draw_centered_surface(screen, surface, y):
    screen.blit(surface, (400 - surface.get_width() // 2, y))


def draw_instructions(screen):
    instructions_text = [
        "Управление:",
        "Стрелка влево - двигать влево",
        "Стрелка вправо - двигать вправо",
        "Стрелка вниз - двигать вниз",
        "Стрелка вверх - поворот",
        "P - пауза"
    ]
    font = pygame.font.Font(None, 20)
    for i, line in enumerate(instructions_text):
        text_surface = font.render(line, True, (255, 255, 255))
        # Размещаем инструкции в правом нижнем углу.
        screen.blit(text_surface, (WINDOW_WIDTH - 150, WINDOW_HEIGHT - 100 + i * 20))


def draw_menu(screen):
    # Задаем цвет фона меню
    menu_background_color = (0, 0, 0)  # Черный цвет
    screen.fill(menu_background_color)  # Заполняем экран черным цветом

    font = pygame.font.Font(None, 50)
    title_surface = font.render("Тетис", True, (255, 255, 255))
    start_surface = font.render("Начать игру", True, (255, 255, 255))

    # Отображаем заголовок и кнопку в центре экрана
    screen.blit(title_surface, (WINDOW_WIDTH // 2 - title_surface.get_width() // 2, 100))
    screen.blit(start_surface, (WINDOW_WIDTH // 2 - start_surface.get_width() // 2, 200))


def main():
    pygame.init()
    pygame.display.set_caption("Tetris с PyGame")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    run = True
    paused = False
    game_over = False
    in_menu = True  # Флаг для отслеживания состояния меню

    # Создаем фон.
    background = pygame.Surface(screen.get_size())
    bgcolor = (0, 0, 0)
    background.fill(bgcolor)
    # Рисуем сетку поверх фона.
    draw_grid(background)
    # Это ускоряет блиттинг.
    background = background.convert()

    try:
        font = pygame.font.Font("Roboto-Regular.ttf", 20)
    except OSError:
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
    next_block_text = font.render(
        "Следующая фигура:", True, (255, 255, 255), bgcolor)
    score_msg_text = font.render(
        "Счет:", True, (255, 255, 255), bgcolor)
    game_over_text = font.render(
        "Игра окончена!", True, (255, 220, 0), bgcolor)

    # Константы событий.
    MOVEMENT_KEYS = pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN
    EVENT_UPDATE_CURRENT_BLOCK = pygame.USEREVENT + 1
    EVENT_MOVE_CURRENT_BLOCK = pygame.USEREVENT + 2
    pygame.time.set_timer(EVENT_UPDATE_CURRENT_BLOCK, 1000)
    pygame.time.set_timer(EVENT_MOVE_CURRENT_BLOCK, 100)

    blocks = BlocksGroup()

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break
            elif event.type == pygame.KEYUP:
                if in_menu:
                    if event.key == pygame.K_RETURN:  # Нажатие Enter для начала игры
                        in_menu = False  # Убираем меню
                else:
                    if not paused and not game_over:
                        if event.key in MOVEMENT_KEYS:
                            blocks.stop_moving_current_block()
                        elif event.key == pygame.K_UP:
                            blocks.rotate_current_block()
                    if event.key == pygame.K_p:
                        paused = not paused

            # Останавливаем движение блоков, если игра окончена или приостановлена.
            if game_over or paused or in_menu:
                continue

            if event.type == pygame.KEYDOWN:
                if event.key in MOVEMENT_KEYS:
                    blocks.start_moving_current_block(event.key)

            try:
                if event.type == EVENT_UPDATE_CURRENT_BLOCK:
                    blocks.update_current_block()
                elif event.type == EVENT_MOVE_CURRENT_BLOCK:
                    blocks.move_current_block()
            except TopReached:
                game_over = True

        # Рисуем фон и сетку.
        if in_menu:
            draw_menu(screen)  # Рисуем меню
        else:
            screen.blit(background, (0, 0))  # Рисуем фон только во время игры
            # Блоки.
            blocks.draw(screen)
            # Боковая панель с различной информацией.
            draw_centered_surface(screen, next_block_text, 50)
            draw_centered_surface(screen, blocks.next_block.image, 100)
            draw_centered_surface(screen, score_msg_text, 240)
            score_text = font.render(
                str(blocks.score), True, (255, 255, 255), bgcolor)
            draw_centered_surface(screen, score_text, 270)
            if game_over:
                draw_centered_surface(screen, game_over_text, 360)


# Рисуем инструкции управления в правом нижнем углу.
draw_instructions(screen)

# Обновление.
pygame.display.flip()

pygame.quit()

if name == "main":
    main()
