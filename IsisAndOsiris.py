import numpy
import random
import json
import subprocess
import itertools
import logging
from typing import Dict, Tuple, Optional

LOG_LEVEL = logging.ERROR
logging.basicConfig(format='[%(levelname)s] [%(asctime)s] '
                           '[%(module)s:(%(lineno)d] %(message)s',
                    level=LOG_LEVEL)


class NpEncoder(json.JSONEncoder):
    """Encodes Numpy data, to json string
    """

    def default(self, obj: object) -> object:
        """Default encoder for encoding obj object

        Args:
            obj (object): object to be encoded

        Returns:
            [object]: json encodable object
        """
        if isinstance(obj, numpy.integer):
            return int(obj)
        elif isinstance(obj, numpy.floating):
            return float(obj)
        elif isinstance(obj, numpy.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


class Player:
    def __init__(self):
        # You may initialise class attributes here...
        pass

    def play(self,
             board: numpy.ndarray,
             cur_player: str,
             players: Dict[str, Dict[str, int | Dict[int, int]]],
             scores: Dict['Player', int]) -> Tuple[Tuple[int, int], int]:
        """Play one move in the game

        Args:
            board (numpy.ndarray): Current board positions
            cur_player: Name of the current player (key for players dict)
            players (dict): Stones and Tiles for all players
            scores (dict): Current scores for all players

        Returns:
            tuple: ((x: int, y: int) position of the move,
                    item: int 0 for stone, tile value for tile.)
        """
        # You may add your Python code here or... call subprocess.Popen()
        # and pass a json string via stdin like this:
        json_input = json.dumps([board, cur_player, players, scores],
                                cls=NpEncoder)
        p = subprocess.Popen(['some_command_to_run_your_bot'],
                             stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        return json.loads(p.communicate(input=json_input.encode())[0])


class RandomPlayer(Player):
    def play(self,
             board: numpy.ndarray,
             cur_player: str,
             players: Dict[str, Dict[str, int | Dict[int, int]]],
             scores: Dict[Player, int]) -> Tuple[Tuple[int, int], int]:

        # Check which positions are free and choose one of them at random
        indices = [(x, y) for (x, y), val in numpy.ndenumerate(board)
                   if val is None]
        play_position = random.choice(indices)

        # Choose a random play, but select another if that move isn't valid
        play = random.choice(['Tiles', 'Stones'])
        if play == 'Tiles' and not sum(players[cur_player][play].values()):
            play = 'Stones'
        elif play == 'Stones' and players[cur_player][play] == 0:
            play = 'Tiles'

        # If play == 'Tiles', select one of the remaining tiles
        if play == 'Tiles':
            tile = random.choice(
                [k for k in players[cur_player]['Tiles']
                 if players[cur_player]['Tiles'][k] > 0])
        else:
            tile = 0

        return (play_position, tile)


class Game:
    """Isis and Osiris game

    Note:
        internal player representation is a dict, with the actual player
        object instance as key. If the dict of players is passed to the Player
        class, the player object is replaced by the player's class name.
        This is to prevent obuse of the other player .play() mechanism to
        anticipate on other player's moves.
    """
    MAX_TILE_VALUE = 4
    DEFAULT_BOARDLEN = 8

    def __init__(self, boardlen: int = DEFAULT_BOARDLEN,
                 player1: Player | None = None,
                 player2: Player | None = None):
        """Initialize a new Isis and Osiris game

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
        """
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
        """Resets the game.

        Args:
            player1 (Player): First player.
            player2 (Player): Second player.

        Notes:
            player1 and player2 *must* provide the .play() method, with the
            arguments given by the Player template class.
        """

        num_items = self.boardlen ** 2 // 4
        self.tiles = {}
        for i, t in enumerate(range(1, self.MAX_TILE_VALUE + 1)):
            tiles_left = num_items - sum(self.tiles.values())
            self.tiles[t] = tiles_left // (2 * (self.MAX_TILE_VALUE - i))
            self.tiles[-t] = self.tiles[t]

        logging.debug(f'Reset game.')

    def add_players(self, player1: Player, player2: Player) -> None:
        """Adds the players to the game. Players must be _instances_ of Player
        player1 is the first player to play (and thus, player 2 is the last)
        This method also initializes the players (sets Stones and Tiles)

        Args:
            player1 (Player): First player.
            player2 (Player): Second player.

        Raises:
            ValueError: if the player doesn't have a .play() method
        """
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
        """Plays a full game between player1 and player2 on a boardlen board

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
        """
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
        """Play a tournament where each player place twice against all others

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
        """
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
        """Plays one move

        Args:
            position (Tuple[int, int]): Board position that is played
            item (int, optional): Item that is played. If 0, a stone is played;
                                  or a tile with the value item. Defaults to 0.

        Raises:
            IndexError: if position is not a valid board position
            ValueError: - if the position is already taken or
                        - if a Stone/Tile is played that player doesn't have
        """
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
        """Returns the score of all players

        Returns:
            Dict[Player, int]: score for each Player object
        """
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
        """Returns True if the game is over and False if it isn't

        Returns:
            bool: True if the game is over and False if it isn't
        """
        n = numpy.sum(self.board == numpy.array(None))
        logging.debug(f'{n} / {self.boardlen ** 2} board positions empty')
        return n == 0

    def __str__(self) -> str:
        """Printable version of the board, players state and current score

        Returns:
            str: string representation of the game, players state and score
        """
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
