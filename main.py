import pygame

from sandbox.config import (
    BACKGROUND_COLOR,
    FPS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)


def main() -> None:
    """Boot Pygame, open the window, and run the main loop."""
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BACKGROUND_COLOR)
        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()