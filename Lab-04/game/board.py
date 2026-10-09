import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:
   
    def __init__(self, color, target_row, col, special_type=None):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.special_type = special_type
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.cascade_count = 0
        self.reset()

    def reset(self):
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        self.cascade_count = 0
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y  
                self.grid[r][c] = gem

        self.resolve_matches()
        self.cascade_count = 0

    def is_animating(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_match_groups(self):
        groups = []

        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                end = c + 1
                while (
                    end < GRID_SIZE
                    and self.grid[r][c]
                    and self.grid[r][end]
                    and self.grid[r][c].color == self.grid[r][end].color
                ):
                    end += 1
                if end - c >= 3:
                    groups.append(([(r, col) for col in range(c, end)], "horizontal"))
                c = end

        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                end = r + 1
                while (
                    end < GRID_SIZE
                    and self.grid[r][c]
                    and self.grid[end][c]
                    and self.grid[r][c].color == self.grid[end][c].color
                ):
                    end += 1
                if end - r >= 3:
                    groups.append(([(row, c) for row in range(r, end)], "vertical"))
                r = end

        return groups

    def find_matches(self):
        matched = set()
        for positions, _ in self.find_match_groups():
            matched.update(positions)
        return matched

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem

    def resolve_matches(self, score_cascades=False, create_special=False):
        total_cleared = 0
        self.cascade_count = 0
        while True:
            matches = self.find_matches()
            if not matches:
                break
            self.cascade_count += 1

            special_position = None
            if create_special and self.cascade_count == 1:
                groups = self.find_match_groups()
                special_groups = [
                    group for group in groups
                    if len(group[0]) >= 4 and not any(
                        self.grid[r][c].special_type for r, c in group[0]
                    )
                ]
                if special_groups:
                    positions, orientation = max(
                        special_groups,
                        key=lambda group: (len(group[0]), group[1] == "horizontal"),
                    )
                    special_position = positions[len(positions) // 2]
                    special_gem = self.grid[special_position[0]][special_position[1]]
                    special_gem.special_type = orientation

            clear_positions = set(matches)
            activated_specials = set()
            pending_specials = [
                position for position in clear_positions
                if self.grid[position[0]][position[1]].special_type
                and position != special_position
            ]
            while pending_specials:
                position = pending_specials.pop()
                if position in activated_specials:
                    continue
                activated_specials.add(position)
                gem = self.grid[position[0]][position[1]]
                if gem.special_type == "horizontal":
                    line_positions = [(position[0], c) for c in range(GRID_SIZE)]
                else:
                    line_positions = [(r, position[1]) for r in range(GRID_SIZE)]
                for line_position in line_positions:
                    if line_position not in clear_positions:
                        clear_positions.add(line_position)
                    line_gem = self.grid[line_position[0]][line_position[1]]
                    if (
                        line_gem
                        and line_gem.special_type
                        and line_position != special_position
                    ):
                        pending_specials.append(line_position)

            clear_positions.discard(special_position)
            total_cleared += len(clear_positions)
            if score_cascades:
                self.score += len(clear_positions) * 10 * self.cascade_count
            for r, c in clear_positions:
                self.grid[r][c] = None
            self.drop_and_refill()
        return total_cleared

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        if not matches:
            self.swap_gems(pos1, pos2)
            return False

        self.moves_remaining -= 1
        self.resolve_matches(score_cascades=True, create_special=True)
        return True

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    if gem.special_type:
                        center = (x + TILE_SIZE // 2, int(y + TILE_SIZE // 2))
                        pygame.draw.circle(
                            surface, (255, 255, 210), center, TILE_SIZE // 2 - 3, width=3
                        )
                        if gem.special_type == "horizontal":
                            pygame.draw.line(
                                surface, (255, 255, 255),
                                (x + 10, center[1]), (x + TILE_SIZE - 10, center[1]), width=3
                            )
                        else:
                            pygame.draw.line(
                                surface, (255, 255, 255),
                                (center[0], int(y) + 10),
                                (center[0], int(y) + TILE_SIZE - 10), width=3
                            )

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )
