"""A small, asset-free 2D creature-catching game prototype.

Controls:
    Arrow keys / WASD - move
    1                - attack during a battle
    2                - throw a capture orb
    3                - run from a battle
    Escape           - quit
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass

import pygame


WIDTH, HEIGHT = 960, 640
WORLD_RECT = pygame.Rect(32, 32, WIDTH - 64, HEIGHT - 112)
FPS = 60

GRASS = (88, 170, 76)
GRASS_DARK = (58, 132, 64)
PATH = (219, 190, 130)
WATER = (82, 166, 220)
WALL = (102, 78, 62)
TEXT = (245, 245, 235)
PANEL = (28, 35, 45)


@dataclass
class Creature:
    """The data needed to display and battle one creature."""

    name: str
    max_hp: int
    hp: int
    color: tuple[int, int, int]


CREATURES = (
    ("Emberfox", 32, (230, 100, 55)),
    ("Mossling", 38, (90, 180, 90)),
    ("Aquafin", 35, (70, 145, 220)),
)


def make_creature() -> Creature:
    """Create a random wild creature at full health."""
    name, hp, color = random.choice(CREATURES)
    return Creature(name, hp, hp, color)


def draw_text(surface: pygame.Surface, message: str, position: tuple[int, int], size: int = 24) -> None:
    """Render one line of UI text at the requested position."""
    font = pygame.font.Font(None, size)
    surface.blit(font.render(message, True, TEXT), position)


def draw_creature(surface: pygame.Surface, creature: Creature, center: tuple[int, int], scale: int) -> None:
    """Draw a simple creature from shapes, so no image assets are required."""
    x, y = center
    pygame.draw.circle(surface, creature.color, (x, y), scale)
    pygame.draw.circle(surface, (35, 35, 35), (x - scale // 3, y - scale // 5), max(4, scale // 10))
    pygame.draw.circle(surface, (35, 35, 35), (x + scale // 3, y - scale // 5), max(4, scale // 10))
    pygame.draw.arc(surface, (35, 35, 35), (x - scale // 2, y, scale, scale // 2), 0.2, 2.9, 3)


def draw_world(surface: pygame.Surface, player: pygame.Rect, obstacles: list[pygame.Rect]) -> None:
    """Render the exploration map, player, and solid obstacles."""
    surface.fill((35, 105, 65))
    pygame.draw.rect(surface, GRASS, WORLD_RECT)

    for x in range(WORLD_RECT.left + 20, WORLD_RECT.right, 48):
        for y in range(WORLD_RECT.top + 20, WORLD_RECT.bottom, 48):
            pygame.draw.line(surface, GRASS_DARK, (x, y), (x + 5, y - 8), 2)

    pygame.draw.rect(surface, PATH, (80, 270, 800, 72))
    pygame.draw.rect(surface, PATH, (440, 64, 72, 400))
    pygame.draw.rect(surface, WATER, (650, 75, 180, 125), border_radius=18)

    for obstacle in obstacles:
        pygame.draw.rect(surface, WALL, obstacle, border_radius=5)

    pygame.draw.rect(surface, (235, 210, 80), player, border_radius=6)
    pygame.draw.circle(surface, (70, 120, 220), (player.centerx, player.top + 7), 8)


def collides(rect: pygame.Rect, obstacles: list[pygame.Rect]) -> bool:
    """Keep the player inside the map and out of obstacles."""
    return not WORLD_RECT.contains(rect) or any(rect.colliderect(obstacle) for obstacle in obstacles)


def run_game() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Creature Trails")
    clock = pygame.time.Clock()

    player = pygame.Rect(120, 210, 28, 28)
    obstacles = [
        pygame.Rect(90, 80, 170, 52),
        pygame.Rect(575, 410, 230, 58),
        pygame.Rect(735, 240, 90, 120),
        pygame.Rect(285, 410, 110, 95),
    ]
    state = "world"
    wild: Creature | None = None
    message = "Explore the tall grass to find a wild creature!"
    encounter_cooldown = 0
    running = True

    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif state == "battle" and wild is not None:
                    if event.key == pygame.K_1:
                        # Attacks reduce health by a random amount.
                        damage = random.randint(6, 12)
                        wild.hp = max(0, wild.hp - damage)
                        if wild.hp == 0:
                            message = f"You won! {wild.name} ran away."
                            state = "world"
                            encounter_cooldown = 1.5
                        else:
                            message = f"Your attack dealt {damage} damage."
                    elif event.key == pygame.K_2:
                        # A capture attempt succeeds 45% of the time.
                        if random.random() < 0.45:
                            message = f"You captured {wild.name}!"
                            state = "world"
                            encounter_cooldown = 1.5
                        else:
                            message = "The creature broke free!"
                    elif event.key == pygame.K_3:
                        message = "You escaped safely."
                        state = "world"
                        encounter_cooldown = 1.5

        if state == "world":
            keys = pygame.key.get_pressed()
            # Build a direction vector from the currently held movement keys.
            direction = pygame.Vector2(
                int(keys[pygame.K_RIGHT] or keys[pygame.K_d])
                - int(keys[pygame.K_LEFT] or keys[pygame.K_a]),
                int(keys[pygame.K_DOWN] or keys[pygame.K_s])
                - int(keys[pygame.K_UP] or keys[pygame.K_w]),
            )
            if direction.length_squared():
                # Normalizing keeps diagonal movement from being faster.
                direction = direction.normalize() * 220 * dt
                candidate = player.move(round(direction.x), round(direction.y))
                if not collides(candidate, obstacles):
                    player = candidate

            encounter_cooldown = max(0, encounter_cooldown - dt)
            in_grass = player.colliderect(pygame.Rect(32, 32, 408, 238))
            # Encounters happen randomly while exploring the grass.
            if in_grass and encounter_cooldown == 0 and random.random() < 0.012:
                wild = make_creature()
                state = "battle"
                message = "A wild creature appeared!"

        # Render a different screen depending on whether the player is exploring or battling.
        if state == "world":
            draw_world(screen, player, obstacles)
            pygame.draw.rect(screen, PANEL, (0, HEIGHT - 80, WIDTH, 80))
            draw_text(screen, message, (24, HEIGHT - 66), 24)
            draw_text(screen, "Move: WASD / arrows   |   Explore the grass   |   Esc: quit", (24, HEIGHT - 35), 20)
        else:
            screen.fill((55, 80, 115))
            pygame.draw.rect(screen, (125, 185, 105), (0, 350, WIDTH, 290))
            pygame.draw.ellipse(screen, (100, 150, 85), (590, 245, 270, 90))
            pygame.draw.ellipse(screen, (100, 150, 85), (80, 390, 300, 90))
            if wild is not None:
                draw_creature(screen, wild, (720, 210), 75)
                draw_text(screen, wild.name, (625, 105), 34)
                pygame.draw.rect(screen, (45, 45, 45), (625, 145, 190, 18))
                pygame.draw.rect(screen, (70, 205, 95), (625, 145, 190 * wild.hp // wild.max_hp, 18))
                draw_text(screen, f"{wild.hp}/{wild.max_hp} HP", (625, 170), 20)
            draw_creature(screen, Creature("You", 1, 1, (235, 210, 80)), (220, 350), 62)
            pygame.draw.rect(screen, PANEL, (0, 530, WIDTH, 110))
            draw_text(screen, message, (24, 545), 24)
            draw_text(screen, "1 Attack    2 Capture orb (45%)    3 Run", (24, 580), 22)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    run_game()
