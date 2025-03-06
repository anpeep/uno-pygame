import random
from typing import List, Dict, Optional, TypeVar

from application.types import GameCheat, Result, success, error

T = TypeVar('T')


# Fisher-Yates shuffle algorithm
def shuffle(array: List[T]) -> List[T]:
    """Shuffle array in-place using Fisher-Yates algorithm."""
    array_copy = array.copy()
    m = len(array_copy)

    while m:
        i = random.randint(0, m - 1)
        m -= 1
        array_copy[m], array_copy[i] = array_copy[i], array_copy[m]

    return array_copy


class GameLogic:
    def __init__(self):
        self.game_state = {
            "current_player_index": 0,
            "deck": [],
            "discard": [],
            "is_reversed": False,
            "players": []
        }

    @staticmethod
    def create_cards() -> List[Dict]:
        colors = ["Blue", "Green", "Red", "Yellow"]
        faces = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "Skip", "Reverse", "Draw Two"]
        wild_faces = ["Wild", "Wild Draw Four"]
        cards = []

        def add_card(color, face):
            cards.append({"color": color, "face": face, "id": len(cards)})

        for color in colors:
            for face in faces:
                add_card(color, face)
                if face != "0":
                    add_card(color, face)

        for face in wild_faces:
            wild_card_face_amount = 4
            for _ in range(wild_card_face_amount):
                add_card("Wild", face)

        return cards

    @staticmethod
    def distribute_cards(players, cards):
        for player in players:
            player["hand"] = cards[0:7]
            del cards[0:7]

    def is_reversed(self) -> bool:
        return self.game_state["is_reversed"]

    def reset(self) -> None:
        self.game_state["current_player_index"] = 0
        self.game_state["deck"] = []
        self.game_state["discard"] = []
        self.game_state["is_reversed"] = False
        self.game_state["players"] = []

    def start_game(self, player_ids: List[str]) -> None:
        players = [{"hand": [], "has_played_card": False, "has_said_uno": False, "id": pid} for pid in player_ids]
        self.game_state["players"] = shuffle(players)

        cards = GameLogic.create_cards()
        self.game_state["deck"] = shuffle(cards)

        GameLogic.distribute_cards(self.game_state["players"], self.game_state["deck"])

    def get_players(self) -> List[Dict]:
        return self.game_state["players"].copy()

    def get_player_cards(self, user_id: str) -> List[Dict]:
        player = next((p for p in self.game_state["players"] if p["id"] == user_id), None)
        if player is None:
            raise ValueError("Player not found")
        return player["hand"]

    def get_top_card(self) -> Optional[Dict]:
        if len(self.game_state["discard"]) == 0:
            return None
        return self.game_state["discard"][-1]

    def get_deck_cards(self) -> List[Dict]:
        return self.game_state["deck"].copy()

    def get_discard_cards(self) -> List[Dict]:
        return self.game_state["discard"].copy()

    def get_current_player(self) -> Dict:
        return self.game_state["players"][self.game_state["current_player_index"]]

    def next_turn(self) -> None:
        current_player = self.get_current_player()

        if len(current_player["hand"]) == 1 and not current_player["has_said_uno"]:
            self.draw_cards(current_player, 2)

        current_player["has_played_card"] = False
        current_player["has_said_uno"] = False

        self.game_state["current_player_index"] = self.game_state["players"].index(self.get_next_player())

    def can_play_card(self, card: Dict, player_id: str) -> bool:
        if len(self.game_state["discard"]) == 0:
            return True

        top_card = self.game_state["discard"][-1]
        print(top_card)
        can_play_others = (card["color"] == top_card["color"] or
                           card["face"] == top_card["face"] or
                           card["color"] == "Wild")
        return can_play_others

    def play_card(self, player_id: str, card_id: int) -> Result:
        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if player is None:
            raise ValueError("Player not found")

        if player["id"] != self.get_current_player()["id"]:
            return error("Not the player's turn")

        if player["has_played_card"]:
            return error("Player has already played a card")

        card_index = next((i for i, card in enumerate(player["hand"]) if card["id"] == card_id), -1)
        if card_index == -1:
            return error("Card not found in player's hand")

        card = player["hand"][card_index]
        if not self.can_play_card(card, player_id):
            return error("Cannot play this card")

        player["hand"].pop(card_index)
        self.game_state["discard"].append(card)
        player["has_played_card"] = True

        if card["face"] == "Wild Draw Four":
            self.draw_cards(self.get_next_player(), 4)
        elif card["face"] == "Wild Draw Eight":
            self.draw_cards(self.get_next_player(), 8)
            self.next_turn()
        elif card["face"] == "Reverse":
            self.game_state["is_reversed"] = not self.game_state["is_reversed"]
        elif card["face"] == "Skip":
            self.next_turn()
        elif card["face"] == "Draw Two":
            self.draw_cards(self.get_next_player(), 2)
            self.next_turn()

        self.next_turn()
        return success(None)

    def change_wild_card_color(self, card_id: int, new_color: str) -> Result:
        last_card = self.game_state["discard"][-1]
        if last_card["id"] != card_id:
            return error("Last card is not this one.")

        if last_card["color"] != "Wild":
            raise ValueError("Last card in deck is not a Wild card")

        last_card["color"] = new_color
        return success(None)

    def draw_card(self, player_id: str) -> Result:
        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if player is None:
            raise ValueError("Player not found")

        if player["id"] != self.get_current_player()["id"]:
            return error("Not the player's turn")

        if player["has_played_card"]:
            return error("Player has already played a card")

        self.draw_cards(player, 1)
        player["has_played_card"] = True

        self.next_turn()
        return success(None)

    def is_winner(self, id: str) -> bool:
        player = next((p for p in self.game_state["players"] if p["id"] == id), None)
        if player is None:
            raise ValueError("Player not found")

        return len(player["hand"]) == 0

    def say_uno(self, id: str) -> Result:
        player = next((p for p in self.game_state["players"] if p["id"] == id), None)
        if player is None:
            raise ValueError("Player not found")

        if player["has_said_uno"]:
            return error("Player has already called UNO")

        if len(player["hand"]) != 2:
            return error("Player cannot call UNO unless they have exactly two cards")

        player["has_said_uno"] = True
        return success(None)

    def activate_cheat_code(self, player_id: str, game_cheat: GameCheat) -> Result:
        if len(self.game_state["players"]) == 0:
            return error("Game has not started yet")

        player = next((p for p in self.game_state["players"] if p["id"] == player_id), None)
        if player is None:
            raise ValueError("Player not found")

        if game_cheat == GameCheat.GIVE_WILD_FOUR:
            new_card_id = random.randint(10000, 10000000)
            new_card = {"color": "Wild", "face": "Wild Draw Four", "id": new_card_id}
            player["hand"].append(new_card)
        elif game_cheat == GameCheat.GIVE_WILD_EIGHT:
            new_card_id = random.randint(10000, 10000000)
            new_card = {"color": "Wild", "face": "Wild Draw Eight", "id": new_card_id}
            player["hand"].append(new_card)
        else:
            return error("Invalid cheat code")

        return success(None)

    def draw_cards(self, player: Dict, count: int) -> None:
        for _ in range(count):
            if len(self.game_state["deck"]) == 0:
                discard_pile = self.game_state["discard"][:-1]
                self.game_state["deck"] = shuffle(discard_pile)
                self.game_state["discard"] = self.game_state["discard"][-1:]

                for card in self.game_state["deck"]:
                    if card["face"].startswith("Wild"):
                        card["color"] = "Wild"

            if self.game_state["deck"]:
                card = self.game_state["deck"].pop()
                player["hand"].append(card)

    def get_next_player(self) -> Dict:
        players_count = len(self.game_state["players"])
        if self.game_state["is_reversed"]:
            next_index = (self.game_state["current_player_index"] - 1) % players_count
        else:
            next_index = (self.game_state["current_player_index"] + 1) % players_count
        return self.game_state["players"][next_index]
