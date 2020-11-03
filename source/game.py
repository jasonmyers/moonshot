import random
import sys
from functools import lru_cache
from typing import List, Sequence

import pygame
from pygame import Vector2
from pygame.sprite import Sprite, collide_mask

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 320, 240

DIRECTION_KEYS = {
    pygame.K_UP,
    pygame.K_DOWN,
    pygame.K_LEFT,
    pygame.K_RIGHT,
}


clock = pygame.time.Clock()


def clamp(value, mn, mx):
    return max(min(value, mx), mn)


class State:
    duration: float = 0.

    actors: List[Sprite]
    player: Sprite
    enemies: List[Sprite]

state = State()


def load_sheet(path: str, rows: int, columns: int) -> List[List[pygame.surface.Surface]]:
    sheet = pygame.image.load(path)
    width, height = sheet.get_width(), sheet.get_height()

    size = Vector2(width // columns, height // rows)

    if columns * size[0] != width or rows * size[1] != height:
        raise ValueError('Dimensions of given image do not cleanly match rows and columns')

    sprites = []
    for column in range(columns):
        col_sprites = []
        for row in range(rows):
            sprite_coord = Vector2(column * size[0], row * size[1])
            sprite_rect = pygame.Rect(*sprite_coord, *size)
            col_sprites.append(
                sheet.subsurface(sprite_rect)
            )
            # sprite = pygame.surface.Surface(size, pygame.SRCALPHA)
            # sprite.blit(sheet, (0, 0), )
            # sprites.append(sprite)
        sprites.append(col_sprites)
    return sprites


class Player(Sprite):
    image: pygame.surface.Surface
    mask: pygame.mask.Mask
    position: Vector2
    velocity: Vector2

    colliding: bool

    MOVE_ACCEL = 2
    START_MOVE_SPEED = 1
    MAX_MOVE_SPEED = 2

    def __init__(self, x: int = 0, y: int = 0) -> None:
        super().__init__()

        self.standing_anim = load_sheet('/Users/gamedev/projects/moonshot/assets/images/player_still.png', 3, 1)
        self.walking_anim = load_sheet('/Users/gamedev/projects/moonshot/assets/images/player_walking.png', 3, 6)

        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.colliding = False

        self.moving = False
        self.move_start = None

        self.size = Vector2(32, 32)
        self.width, self.height = self.size

    @property
    def image(self):
        image = pygame.surface.Surface(self.size, flags=pygame.SRCALPHA)

        if self.moving:

            current_time = pygame.time.get_ticks()
            progress = current_time - self.move_start

            anim_index = (progress % 600) // 100
            for sprite in self.walking_anim[anim_index]:
                image.blit(sprite, (0, 0))

        else:
            for sprite in self.standing_anim[0]:
                image.blit(sprite, (0, 0))

        self.mask = pygame.mask.from_surface(image)
        return image

    @property
    def rect(self) -> pygame.rect.Rect:
        return self._rect(self.x, self.y)

    @lru_cache(maxsize=1)
    def _rect(self, x: float, y: float) -> pygame.rect.Rect:  # noqa
        return pygame.rect.Rect(
            int(self.x), int(self.y),
            self.width, self.height
        )

    def move(self) -> None:
        self.position += self.velocity

    def update(self, dt: float, events: List[pygame.event.Event], pressed_keys: Sequence[bool]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.moving = True
                    self.move_start = pygame.time.get_ticks()
                    self.velocity[0] = clamp(self.velocity[0], Player.START_MOVE_SPEED, Player.MAX_MOVE_SPEED)
                if event.key == pygame.K_LEFT:
                    self.moving = True
                    self.move_start = pygame.time.get_ticks()
                    self.velocity[0] = clamp(self.velocity[0], -Player.MAX_MOVE_SPEED, -Player.START_MOVE_SPEED)
                if event.key == pygame.K_DOWN:
                    self.moving = True
                    self.move_start = pygame.time.get_ticks()
                    self.velocity[1] = clamp(self.velocity[1], Player.START_MOVE_SPEED, Player.MAX_MOVE_SPEED)
                if event.key == pygame.K_UP:
                    self.moving = True
                    self.move_start = pygame.time.get_ticks()
                    self.velocity[1] = clamp(self.velocity[1], -Player.MAX_MOVE_SPEED, -Player.START_MOVE_SPEED)

        if pressed_keys[pygame.K_RIGHT]:
            self.velocity[0] += Player.MOVE_ACCEL * dt
        if pressed_keys[pygame.K_LEFT]:
            self.velocity[0] -= Player.MOVE_ACCEL * dt
        if pressed_keys[pygame.K_DOWN]:
            self.velocity[1] += Player.MOVE_ACCEL * dt
        if pressed_keys[pygame.K_UP]:
            self.velocity[1] -= Player.MOVE_ACCEL * dt

        if not any(pressed_keys[key] for key in DIRECTION_KEYS):
            self.velocity /= (2 / dt)
            self.moving = False
            self.move_start = None

        self.velocity[0] = clamp(self.velocity[0], -Player.MAX_MOVE_SPEED, Player.MAX_MOVE_SPEED)
        self.velocity[1] = clamp(self.velocity[1], -Player.MAX_MOVE_SPEED, Player.MAX_MOVE_SPEED)

        self.move()

        if self.left < 0 or self.right > WINDOW_WIDTH:
            self.velocity[0] = -self.velocity[0]
        if self.top < 0 or self.bottom > WINDOW_HEIGHT:
            self.velocity[1] = -self.velocity[1]

        self.colliding = any(
            bool(collide_mask(self, enemy))
            for enemy in state.enemies
        )

    def draw(self, screen) -> None:
        screen.blit(self.image, self.rect)

    @property
    def x(self) -> float:
        return self.position[0]

    @property
    def y(self) -> float:
        return self.position[1]

    @property
    def left(self) -> int:
        return self.rect.left

    @property
    def right(self) -> int:
        return self.rect.right

    @property
    def top(self) -> int:
        return self.rect.top

    @property
    def bottom(self) -> int:
        return self.rect.bottom


def main():
    pygame.init()

    blank = pygame.color.Color('#1b211b')

    screen = pygame.display.set_mode(WINDOW_SIZE, flags=pygame.SCALED)

    state.player = Player()
    state.enemies = [
    ]
    state.actors = [state.player, *state.enemies]

    FPS = 60

    while True:
        dt = clock.tick(FPS) / 1000.

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    sys.exit()

        pressed_keys = pygame.key.get_pressed()

        for actor in state.actors:
            actor.update(dt, events, pressed_keys)

        screen.fill(blank)

        for actor in state.actors:
            actor.draw(screen)

        pygame.display.flip()


if __name__ == '__main__':
    main()
