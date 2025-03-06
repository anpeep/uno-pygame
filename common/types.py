from typing import TypedDict, List, Literal, Union

# Define the card color and face literals
CardColor = Literal["Blue", "Green", "Red", "Yellow", "Wild"]
CardFace = Literal[
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", 
    "Skip", "Reverse", "Draw Two", 
    "Wild", "Wild Draw Four", "Wild Draw Eight"
]

class Card(TypedDict):
    color: CardColor
    face: CardFace
    id: int

class Player(TypedDict):
    hand: List['Card']
    has_played_card: bool  # Converted camelCase to snake_case
    has_said_uno: bool     # Converted camelCase to snake_case
    id: str

class GameState(TypedDict):
    current_player_index: int  # Converted camelCase to snake_case
    deck: List[Card]
    discard: List[Card]
    is_reversed: bool          # Converted camelCase to snake_case
    players: List[Player]
