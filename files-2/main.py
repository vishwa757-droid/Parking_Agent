"""Entry point for the Autonomous Parking Agent simulation."""

import pygame

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    CELL_SIZE,
    GRID_COLS,
    PANEL_WIDTH,
    TEXT_COLOR,
    MUTED_TEXT_COLOR,
    PANEL_COLOR,
    PANEL_LINE_COLOR,
    KEY_COLOR,
    ACCENT_COLOR,
    AGENT_COLOR,
    TRAFFIC_COLOR,
    TARGET_LINE_COLOR,
)
from simulation import Simulation

BACKGROUND_COLOR = (25, 28, 30)

STATUS_COLORS = {
    "SEARCHING": (150, 155, 165),
    "DRIVING": (90, 175, 255),
    "WAITING": (240, 160, 70),
    "PARKED": (110, 220, 130),
    "PAUSED": (240, 200, 80),
}


def draw_text(screen, font, text, x, y, color=TEXT_COLOR):
    screen.blit(font.render(text, True, color), (x, y))


def draw_text_right(screen, font, text, right, y, color=TEXT_COLOR):
    surface = font.render(text, True, color)
    screen.blit(surface, (right - surface.get_width(), y))


def draw_key(screen, font, key, x, y):
    """Draw a small key-cap such as [SPACE]."""
    label = font.render(key, True, TEXT_COLOR)
    rect = pygame.Rect(x, y - 3, max(28, label.get_width() + 14), 22)
    pygame.draw.rect(screen, KEY_COLOR, rect, border_radius=5)
    pygame.draw.rect(screen, PANEL_LINE_COLOR, rect, 1, border_radius=5)
    screen.blit(label, label.get_rect(center=rect.center))


def agent_status(simulation):
    agent = simulation.agent
    if simulation.paused:
        return "PAUSED"
    if agent.parked:
        return "PARKED"
    if agent.target is None:
        return "SEARCHING"
    if agent.waiting:
        return "WAITING"
    return "DRIVING"


def draw_panel(screen, fonts, simulation):
    title_font, font, small_font = fonts
    stats = simulation.statistics()

    panel_x = GRID_COLS * CELL_SIZE
    left = panel_x + 20
    right = panel_x + PANEL_WIDTH - 20

    # Panel background.
    pygame.draw.rect(screen, PANEL_COLOR, (panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT))
    pygame.draw.line(screen, PANEL_LINE_COLOR, (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)

    # Title.
    draw_text(screen, title_font, "AUTONOMOUS", left, 24)
    draw_text(screen, title_font, "PARKING AGENT", left, 48, ACCENT_COLOR)
    pygame.draw.line(screen, PANEL_LINE_COLOR, (left, 82), (right, 82), 1)

    # Status chip.
    draw_text(screen, small_font, "STATUS", left, 98, MUTED_TEXT_COLOR)
    status = agent_status(simulation)
    chip = pygame.Rect(left, 118, right - left, 30)
    pygame.draw.rect(screen, STATUS_COLORS[status], chip, border_radius=8)
    label = font.render(status, True, (20, 22, 26))
    screen.blit(label, label.get_rect(center=chip.center))

    # Stats.
    draw_text(screen, small_font, "STATS", left, 166, MUTED_TEXT_COLOR)
    minutes, seconds = divmod(int(stats["time"]), 60)
    target = stats["target"]
    rows = [
        ("Time", f"{minutes:02d}:{seconds:02d}"),
        ("Cars driving", str(stats["traffic_cars"])),
        ("Cars parked", str(stats["parked_cars"])),
        ("Re-plans", str(stats["replans"])),
        ("Target bay", f"({target[0]}, {target[1]})" if target else "-"),
    ]
    for i, (name, value) in enumerate(rows):
        y = 188 + i * 24
        draw_text(screen, font, name, left, y, MUTED_TEXT_COLOR)
        draw_text_right(screen, font, value, right, y)

    # Controls.
    draw_text(screen, small_font, "CONTROLS", left, 324, MUTED_TEXT_COLOR)
    controls = [
        ("SPACE", "Pause"),
        ("R", "Reset"),
        ("N", "Add car"),
        ("S", "New scenario"),
        ("ESC", "Quit"),
    ]
    for i, (key, action) in enumerate(controls):
        y = 348 + i * 26
        draw_key(screen, small_font, key, left, y)
        draw_text(screen, font, action, left + 68, y - 2)

    # Legend.
    draw_text(screen, small_font, "LEGEND", left, 492, MUTED_TEXT_COLOR)
    legend = [
        (AGENT_COLOR, "Parking agent"),
        (TRAFFIC_COLOR, "Traffic"),
        (TARGET_LINE_COLOR, "Target bay"),
    ]
    for i, (color, name) in enumerate(legend):
        y = 514 + i * 22
        pygame.draw.rect(screen, color, (left, y + 2, 14, 14), border_radius=4)
        draw_text(screen, font, name, left + 24, y)


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Autonomous Parking Agent")

    clock = pygame.time.Clock()
    fonts = (
        pygame.font.Font(None, 28),
        pygame.font.Font(None, 22),
        pygame.font.Font(None, 18),
    )

    simulation = Simulation()

    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    simulation.paused = not simulation.paused

                elif event.key == pygame.K_r:
                    simulation.reset()

                elif event.key == pygame.K_n:
                    simulation.add_random_car()

                elif event.key == pygame.K_s:
                    simulation.new_random_seed()

        simulation.update(dt)

        screen.fill(BACKGROUND_COLOR)

        # Parking lot, then traffic, then the autonomous agent on top.
        simulation.grid.draw(screen, target=simulation.agent.target)
        simulation.traffic.draw(screen, CELL_SIZE)
        simulation.agent.draw(screen, CELL_SIZE)

        draw_panel(screen, fonts, simulation)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
