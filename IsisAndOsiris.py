import numpy
import numpy.random
import json


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


class Game:
    PLAYER_1 = 'A'
    PLAYER_2 = 'B'
    PLAYERS = (PLAYER_1, PLAYER_2)
    MAX_TILE_VALUE = 4

    board: numpy.ndarray
    boardsize: int
    players: dict
    cur_player: str
    tiles: dict

    def __init__(self, boardsize: int):
        self.boardsize = boardsize
        self.players = {p: {'Stones': 0, 'Tiles': []} for p in self.PLAYERS}
        self.cur_player = self.PLAYER_1
        self.reset_game(boardsize)

    def reset_game(self, boardsize: int):
        if boardsize % 4 != 0:
            raise ValueError(f'Boardsize must be a multiple of 4, '
                             f'not {boardsize}.')

        num_items = boardsize ** 2 // 4
        self.board = numpy.full((boardsize, boardsize), None)
        self.boardsize = boardsize
        self.cur_player = self.PLAYER_1

        self.tiles = {}
        for i, t in enumerate(range(1, self.MAX_TILE_VALUE + 1)):
            tiles_left = num_items - sum(self.tiles.values())
            self.tiles[t] = tiles_left // (2 * (self.MAX_TILE_VALUE - i))
            self.tiles[-t] = self.tiles[t]

        for p in self.PLAYERS:
            self.players[p] = {
                'Stones': num_items,
                'Tiles': dict(self.tiles)
            }

    def play(self, position: tuple, item: int = 0):
        try:
            cur_value = self.board[position]
        except IndexError:
            raise IndexError(f'Position {position} is not a valid position.')

        if cur_value is not None:
            raise ValueError(f'Board at position {position} is already '
                             f'taken with value: {cur_value}.')

        if item == 0 and self.players[self.cur_player]['Stones'] <= 0:
            raise ValueError("You played a stone, but you don't "
                             "have stones left.")

        if item != 0 and item not in self.players[self.cur_player]['Tiles']:
            raise ValueError(f"You played tile {item}, but that is not "
                             f"a valid tile value. You have: "
                             f"{self.players[self.cur_player]['Tiles']}")

        if item != 0 and self.players[self.cur_player]['Tiles'][item] <= 0:
            raise ValueError(f"You played tile {item}, but you don't have "
                             f"tiles with that value. You have: "
                             f"{self.players[self.cur_player]['Tiles']}")

        if item == 0:
            self.board[position] = self.cur_player
            self.players[self.cur_player]['Stones'] -= 1
        else:
            self.board[position] = item
            self.players[self.cur_player]['Tiles'][item] -= 1

        # Advance to the next player
        self.cur_player = self.PLAYERS[(self.PLAYERS.index(
            self.cur_player) + 1) % len(self.PLAYERS)]

    def players_score(self):
        scores = dict(zip(self.PLAYERS, [0] * len(self.PLAYERS)))

        for (x, y), value in numpy.ndenumerate(self.board):
            if value in self.PLAYERS:
                if (x > 0 and
                        isinstance(self.board[x - 1, y], numpy.integer)):
                    scores[value] += self.board[x - 1, y]
                if (x < self.boardsize - 1 and
                        isinstance(self.board[x + 1, y], numpy.integer)):
                    scores[value] += self.board[x + 1, y]
                if (y > 0 and
                        isinstance(self.board[x, y - 1], numpy.integer)):
                    scores[value] += self.board[x, y - 1]
                if (y < self.boardsize - 1 and
                        isinstance(self.board[x, y + 1], numpy.integer)):
                    scores[value] += self.board[x, y + 1]

        return scores

    def finished(self):
        return numpy.all(self.board != numpy.array(None))

    def get_json(self):
        return json.dumps([self.board.tolist(),
                           self.players,
                           self.players_score()],
                          cls=NpEncoder)

    def __str__(self):
        output = 'Board:\n'
        output += str(self.board)
        for p in self.players:
            output += f'\nPlayer {p} has: {self.players[p]}'
        output += f"\nPlayer's scores: {self.players_score()}"

        return output


def main():
    boardsize = 8
    g = Game(boardsize)
    print(g.get_json())

    indices = [(x, y) for x in range(boardsize) for y in range(boardsize)]
    numpy.random.shuffle(indices)
    for coord in indices:
        play = numpy.random.choice(list(g.players[g.cur_player].keys()))
        if play == 'Tiles' and not sum(g.players[g.cur_player][play].values()):
            play = 'Stones'
        elif play == 'Stones' and g.players[g.cur_player][play] == 0:
            play = 'Tiles'

        if play == 'Tiles':
            tile = numpy.random.choice(
                [k for k in g.players[g.cur_player]['Tiles']
                 if g.players[g.cur_player]['Tiles'][k] > 0])
        else:
            tile = 0

        g.play(coord, tile)

    print(g.get_json())
    print(g)


if __name__ == "__main__":
    main()
