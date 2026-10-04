"""Small drawing helpers shared by the grid, traffic and agent."""

import pygame

_sprite_cache = {}


def shade(color, amount):
    """Make a color lighter (+) or darker (-)."""
    return tuple(max(0, min(255, int(c + amount))) for c in color)


def _make_car_sprite(color, cell_size, sensor):
    """Draw a simple top-down car that faces right (east)."""
    length = int(cell_size * 0.66)
    width = int(cell_size * 0.40)
    sprite = pygame.Surface((length, width), pygame.SRCALPHA)

    # Body with a darker outline.
    body = pygame.Rect(0, 0, length, width)
    pygame.draw.rect(sprite, shade(color, -45), body, border_radius=6)
    pygame.draw.rect(sprite, color, body.inflate(-2, -2), border_radius=5)

    # Cabin glass, with the roof sitting on top of it.
    glass = (38, 48, 62)
    cabin = pygame.Rect(int(length * 0.24), 3, int(length * 0.46), width - 6)
    pygame.draw.rect(sprite, glass, cabin, border_radius=3)
    roof = pygame.Rect(int(length * 0.33), 4, int(length * 0.27), width - 8)
    pygame.draw.rect(sprite, shade(color, 25), roof, border_radius=2)

    # Headlights (front) and tail lights (rear).
    light_h = max(2, width // 6)
    for y in (2, width - 2 - light_h):
        pygame.draw.rect(sprite, (255, 240, 170), (length - 4, y, 3, light_h))
        pygame.draw.rect(sprite, (200, 45, 45), (1, y, 3, light_h))

    # A small "sensor" on the roof marks the autonomous car.
    if sensor:
        pygame.draw.circle(sprite, (20, 40, 70), roof.center, 3)
        pygame.draw.circle(sprite, (120, 230, 255), roof.center, 2)

    return sprite


def get_car_sprite(color, angle, cell_size, sensor=False):
    key = (color, angle, cell_size, sensor)
    if key not in _sprite_cache:
        base_key = (color, 0, cell_size, sensor)
        if base_key not in _sprite_cache:
            _sprite_cache[base_key] = _make_car_sprite(color, cell_size, sensor)
        _sprite_cache[key] = pygame.transform.rotate(
            _sprite_cache[base_key], angle
        )
    return _sprite_cache[key]


def draw_car(screen, cell_size, center, angle, color, sensor=False):
    """Draw a car centred on a pixel position, facing `angle` degrees."""
    sprite = get_car_sprite(color, angle, cell_size, sensor)
    x, y = round(center[0]), round(center[1])
    screen.blit(sprite, sprite.get_rect(center=(x, y)))


def draw_path_dots(screen, points, color):
    """Draw a dotted line through a list of pixel points."""
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        pygame.draw.circle(screen, color, (round((ax + bx) / 2), round((ay + by) / 2)), 2)
        pygame.draw.circle(screen, color, (round(bx), round(by)), 3)
