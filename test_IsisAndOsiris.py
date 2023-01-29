import numpy
from pytest import raises

"""
import random
import json
import subprocess
import itertools
import logging
from typing import Dict, Tuple
"""

import IsisAndOsiris as IAO


def test_NpEncoder():
    encoder = IAO.NpEncoder()

    assert isinstance(encoder.default(numpy.intc(12)), int)
    assert isinstance(encoder.default(numpy.float16(12.3)), float)
    assert encoder.default(numpy.ndarray([1, 2, 3]) == [1, 2, 3])


def test_Game_init():
    class NoPlayer:
        pass

    boardlen = 24
    player1 = IAO.Player()
    player2 = IAO.Player()
    no_player = NoPlayer()
    g = IAO.Game(boardlen)
    g.reset_game()
    g.add_players(player1, player2)

    assert g.boardlen == boardlen
    assert all(item == None
               for item in numpy.nditer(g.board, flags=['refs_ok']))
    assert player1 in g.players
    assert player2 in g.players

    with raises(ValueError):
        g.add_players(player1, no_player)


"""
class Game:

    Note:
        internal player representation is a dict, with the actual player
        object instance as key. If the dict of players is passed to the Player
        class, the player object is replaced by the player's class name.
        This is to prevent obuse of the other player .play() mechanism to
        anticipate on other player's moves.
    MAX_TILE_VALUE = 4
    DEFAULT_BOARDLEN = 8

    def __init__(self, boardlen: int = DEFAULT_BOARDLEN,
                 player1: Player | None = None,
                 player2: Player | None = None):

        The Game class has the following attributes:
            board (numpy.ndarray[object]): board array. Elements are:
                None  : empty place on the board
                Player: stone of Player
                int   : card with the corresponding value
            boardlen (int): length of the board sides
            cur_player (Player): current player
            players Dict[Player, Dict[str, int | Dict[int, int]]]: dict with
                Player: player object as key
                Dict[str, int | Dict[int, int]]: dict with:
                    str: either 'Stones' or 'Tiles' as key
                    int: number of strones left (with key: 'Stones')
                    Dict[int, int]: dict with:
                        int: value of a card (1, -1, 2, -2, ...)
                        int: number of cards of that value
            tiles (Dict[int, int]): dict with:
                int: value of a card (1, -1, 2, -2, ...)
                int: number of cards of that value

        Args:
            boardlen (int, optional): board side length.
                                      Defaults to DEFAULT_BOARDLEN.
            player1 (Player, optional): player 1
            player2 (Player, optional): player 2

        Raises:
            ValueError: if the boardlen is not a multiple of 4 or if one of
            the players doesn't have a .play() method.
        if boardlen % 4 != 0:
            raise ValueError(f'boardlen must be a multiple of 4, '
                             f'not {boardlen}.')

        self.board = numpy.full((boardlen, boardlen), None)
        self.boardlen: int = boardlen
        self.cur_player: Player = Player()
        self.players: Dict[Player, Dict[str, object]] = {}
        self.tiles: Dict[int, int] = {}
        self.reset_game()
        self.add_players(player1, player2)
        logging.debug('Initialized game')

    def reset_game(self) -> None:


        Args:
            player1 (Player): First player.
            player2 (Player): Second player.

        Notes:
            player1 and player2 *must* provide the .play() method, with the
            arguments given by the Player template class.


        num_items = self.boardlen ** 2 // 4
        self.tiles = {}
        for i, t in enumerate(range(1, self.MAX_TILE_VALUE + 1)):
            tiles_left = num_items - sum(self.tiles.values())
            self.tiles[t] = tiles_left // (2 * (self.MAX_TILE_VALUE - i))
            self.tiles[-t] = self.tiles[t]

        logging.debug('Reset game.')

    def add_players(self, player1: Player, player2: Player) -> None:

        player1 is the first player to play (and thus, player 2 is the last)
        This method also initializes the players (sets Stones and Tiles)

        Args:
            player1 (Player): First player.
            player2 (Player): Second player.

        Raises:
            ValueError: if the player doesn't have a .play() method

        if len(self.tiles) == 0:
            self.reset_game(self.boardlen)

        for p in (player1, player2):
            if not hasattr(p, 'play'):
                raise ValueError(f'Player {p} does not have a "play" '
                                 f'method, which is needed to play.')

        self.cur_player = player1

        for player in (player1, player2):
            self.players[player] = {
                'Stones': self.boardlen ** 2 // 4,
                'Tiles': dict(self.tiles)
            }
        logging.debug(f'Added players. Players: {self.players}')

    def play_game(self,
                  boardlen: int = DEFAULT_BOARDLEN,
                  player1: Player = None,
                  player2: Player = None) -> Dict[Player, int]:


        Args:
            boardlen (int, optional): Size of the board (width/length).
                                      Defaults to DEFAULT_boardlen.
            player1 (Player, optional): First player. Defaults to None.
            player2 (Player, optional): Second player. Defaults to None.

        Raises:
            ValueError: if player1 and player2 are None and no players are
            known from an earlier call to add_players() or the constructor

        Returns:
            Dict[Player, int]: score for each Player object

        if not player1 or not player2 and len(self.players) < 2:
            raise ValueError('No players were given when play_game was called')

        if not player1 and not player2:
            self.reset_game(boardlen, *self.players)
        else:
            self.reset_game(boardlen, player1, player2)

        while not self.finished():
            self.play_move(*self.cur_player.play(
                self.board,
                str(self.cur_player),
                {str(p): self.players[p] for p in self.players},
                self.players_score()))

        logging.debug(f'Game finished; board: {self.board}')
        scores = self.players_score()
        logging.debug(f'Game played with scores: {scores}')
        return scores

    def play_tournament(self, players: list,
                        boardlen: int = DEFAULT_BOARDLEN) -> Dict[Player, int]:


        Notes:
            - Each player plays against each other player *twice*: once as
              first player (may place first move) and once as second player.
            - Scoring is as follows:
                - 0 points for a loss
                - 1 point for a draw (same score at the end of the game)
                - 2 poinst for a win
            - The play_tournament method iterates multiple times over the
              players object, so providing a players generator will not work.

        Args:
            players (list): list of players
            boardlen (int, optional): Size of the board (width/length).
                                       Defaults to DEFAULT_boardlen.

        Returns:
            Dict[Player, int]: score for each Player object

        t_scores = {p: 0 for p in players}

        for (p1, p2) in itertools.permutations(players, 2):
            logging.info(f'Playing tournament game between {p1} and {p2}')
            game_scores = self.play_game(boardlen, p1, p2)
            logging.info(f'Game result: {game_scores}')
            if game_scores[p1] == game_scores[p2]:
                t_scores[p1] += 1
                t_scores[p2] += 1
            elif game_scores[p1] > game_scores[p2]:
                t_scores[p1] += 2
            else:
                t_scores[p2] += 2
            logging.info(f'Intermediate tournament scores: {t_scores}')

        return t_scores

    def play_move(self, position: Tuple[int, int], item: int = 0) -> None:


        Args:
            position (Tuple[int, int]): Board position that is played
            item (int, optional): Item that is played. If 0, a stone is played;
                                  or a tile with the value item. Defaults to 0.

        Raises:
            IndexError: if position is not a valid board position
            ValueError: - if the position is already taken or
                        - if a Stone/Tile is played that player doesn't have

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
            logging.debug(f"Player {self.cur_player} played 'Stone' "
                          f"at position {position}")
        else:
            self.board[position] = item
            self.players[self.cur_player]['Tiles'][item] -= 1
            logging.debug(f"Player {self.cur_player} played 'Tile' {item}"
                          f"at position {position}")

        # Advance to the next player
        players = list(self.players.keys())
        cur_player_idx = players.index(self.cur_player)
        self.cur_player = players[(cur_player_idx + 1) % len(players)]

    def players_score(self) -> Dict[Player, int]:


        Returns:
            Dict[Player, int]: score for each Player object

        scores = dict.fromkeys(self.players, 0)

        for (x, y), value in numpy.ndenumerate(self.board):
            if value in self.players:
                if (x > 0 and
                        isinstance(self.board[x - 1, y], int)):
                    scores[value] += self.board[x - 1, y]
                if (x < self.boardlen - 1 and
                        isinstance(self.board[x + 1, y], int)):
                    scores[value] += self.board[x + 1, y]
                if (y > 0 and
                        isinstance(self.board[x, y - 1], int)):
                    scores[value] += self.board[x, y - 1]
                if (y < self.boardlen - 1 and
                        isinstance(self.board[x, y + 1], int)):
                    scores[value] += self.board[x, y + 1]

        return scores

    def finished(self) -> bool:


        Returns:
            bool: True if the game is over and False if it isn't

        n = numpy.sum(self.board == numpy.array(None))
        logging.debug(f'{n} / {self.boardlen ** 2} board positions empty')
        return n == 0

    def __str__(self) -> str:


        Returns:
            str: string representation of the game, players state and score

        output = 'Board:\n'
        output += str(self.board)
        for p in self.players:
            output += f'\nPlayer {p} has: {self.players[p]}'
        output += f"\nPlayer's scores: {self.players_score()}"

        return output


def main():
    g = Game()
    num_players = 4
    players = [RandomPlayer() for _ in range(num_players)]
    scores = g.play_tournament(players)
    print(''.join(f'{p.__class__.__name__}: {scores[p]}\n' for p in scores))


if __name__ == "__main__":
    main()
"""
