import asyncio
from typing import List

import discord
from discord import ui, ButtonStyle, File
from discord.ext.commands.context import Context

from application.game_logic import GameLogic
from application.types import GameCheat, error


# TODO: fix win condition

class UnoButtonView(discord.ui.View):
    def __init__(self, game_ui):
        super().__init__(timeout=None)
        self.game_ui = game_ui

    @discord.ui.button(label="Show Cards", custom_id="show-cards-btn", style=discord.ButtonStyle.secondary)
    async def show_cards_button(self, button, interaction):
        await self.game_ui.handle_show_cards_button(interaction)

    @discord.ui.button(label="Draw Card", custom_id="draw-card-btn", style=discord.ButtonStyle.secondary)
    async def draw_card_button(self, button, interaction):
        print("draw card")
        await self.game_ui.handle_draw_card_button(interaction)

    @discord.ui.button(label="Say UNO", custom_id="say-uno-btn", style=discord.ButtonStyle.primary)
    async def say_uno_button(self, button, interaction):
        await self.game_ui.handle_say_uno(interaction)



class GameView(discord.ui.View):
    def __init__(self, game_ui):
        super().__init__(timeout=None)
        self.game_ui = game_ui

    @discord.ui.button(label="Join", custom_id="join-btn", style=discord.ButtonStyle.primary)
    async def join_button(self, button, interaction):
        print("say uno")  # This will now print when button is pressed
        await self.game_ui.handle_join_button(interaction)

    @discord.ui.button(label="Start", custom_id="start-btn", style=discord.ButtonStyle.success)
    async def start_button(self, button, interaction):
        await self.game_ui.handle_start_button(interaction)

    @discord.ui.button(label="Cancel", custom_id="cancel-btn", style=discord.ButtonStyle.danger)
    async def cancel_button(self, button, interaction):
        await self.game_ui.handle_cancel_button(interaction)


class GameUi:
    def __init__(self):
        self.message = None
        self.initiator = None
        self.last_player = None
        self.game_logic = GameLogic()
        self.players = []

        self.action_player_interactions = {"cardSelection": {}, "wildCardColorSelection": {}}

    @staticmethod
    def get_card_label(card: dict) -> str:
        color_emoji = GameUi.get_color_emoji(card["color"])
        return f"{color_emoji}{card['face']}"

    @staticmethod
    def get_color_emoji(color: str) -> str:
        if color == "Wild":
            return "⚫"
        elif color == "Red":
            return "🔴"
        elif color == "Green":
            return "🟢"
        elif color == "Blue":
            return "🔵"
        elif color == "Yellow":
            return "🟡"
        raise ValueError("Unknown color")

    @staticmethod
    def get_card_image_path(card: dict) -> str:
        base_path = "./assets/images/cards"
        face = card["face"].lower().replace(" ", "_")
        return f"{base_path}/card-{card['color'].lower()}-{face}.png"

    async def handle_start(self, ctx: Context) -> None:
        if self.initiator is not None:
            await ctx.send(content="There is already a lobby in progress.", )
            return

        self.initiator = ctx.author
        self.players.append(self.initiator)

        view = GameView(self)
        self.message = await ctx.send(content=self.get_message_content(), view=view)

    async def handle_join_button(self, interaction: discord.Interaction) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user

        if any(player.id == member.id for player in self.players):
            await interaction.response.send_message(content="You have already joined this lobby.", ephemeral=True)

            async def delete_reply():
                try:
                    await interaction.delete_original_response()
                except:
                    pass

            await asyncio.sleep(10)
            await delete_reply()
            return

        self.players.append(member)

        await self.message.edit(content=self.get_message_content())

        if self.initiator is None:
            raise ValueError("Initiator is null")

        await interaction.response.send_message(content=f"You have joined {self.initiator.mention}'s lobby.",
                                                ephemeral=True)

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    async def handle_start_button(self, interaction: discord.Interaction) -> None:
        member = interaction.user

        if self.initiator != member:
            await interaction.response.send_message(content="You are not the initiator.", ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        min_player_amount = 1
        if len(self.players) < min_player_amount:
            await interaction.response.send_message(content=f"Not enough players. Needed amount: {min_player_amount}.",
                                                    ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        if self.message is None:
            raise ValueError("Message is null")

        await self.start_game()

        await interaction.response.send_message(content="Game has started!", ephemeral=True)

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    async def handle_cancel_button(self, interaction: discord.Interaction) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user

        if self.initiator != member:
            await interaction.response.send_message(content="You are not the initiator.", ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await self.message.delete()
        self.reset_game()

        await interaction.response.send_message(content="You have deleted the lobby.", ephemeral=True)

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    async def handle_show_cards_button(self, interaction: discord.Interaction) -> None:
        member = interaction.user
        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], str(member.id))

        cards = self.game_logic.get_player_cards(str(member.id))

        current_player = self.game_logic.get_current_player()
        is_current_player = current_player["id"] == str(member.id)

        view = ui.View()

        card_buttons = []
        for card in cards:
            label = GameUi.get_card_label(card)
            can_play = self.game_logic.can_play_card(card, current_player["id"])

            button = ui.Button(label=label, style=ButtonStyle.secondary, custom_id=f"card-{card['id']}",
                               disabled=not is_current_player or not can_play)
            card_buttons.append(button)

        # draw_card_button = ui.Button(label="Draw Card", style=ButtonStyle.danger, custom_id="draw-card-btn",
        #                              disabled=not is_current_player)
        draw_card_button = ui.Button(
            label="Draw Card",
            style=ButtonStyle.danger,
            custom_id="draw-card-btn-dynamic",  # Different custom_id
            disabled=not is_current_player
        )
        draw_card_button.callback = lambda i: self.handle_draw_card_button(i)  # Explicitly set callback
        card_buttons.append(draw_card_button)

        # Add buttons to the view (needs pagination for more than 25 buttons)
        for button in card_buttons[:25]:  # Discord limits to 25 buttons per message
            view.add_item(button)

        await interaction.response.send_message(content="Your cards:", view=view, ephemeral=True)

        self.add_action_player_interaction("cardSelection", str(member.id), interaction)

    async def handle_card_button(self, interaction: discord.Interaction, card_id: int) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        player_cards = self.game_logic.get_player_cards(str(member.id))
        card = next((c for c in player_cards if c["id"] == card_id), None)

        if not card:
            await interaction.response.send_message(content="Card not found.", ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        if card["color"] == "Wild":
            await self.handle_wild_card_color(card_id, interaction)
            return

        result = self.game_logic.play_card(str(member.id), card_id)

        if hasattr(result, "error") and result.error:
            await interaction.response.send_message(content=result.error, ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        self.last_player = member

        await interaction.response.send_message(content="You played a card.", ephemeral=True)

        await interaction.delete_original_response()

        top_card = self.game_logic.get_top_card()

        embed = self.get_game_message_content()
        files = [File(GameUi.get_card_image_path(top_card))] if top_card else []

        await self.message.edit(embeds=[embed], files=files)

        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], str(member.id))

        is_winner = self.game_logic.is_winner(str(member.id))
        if not is_winner:
            return

        if not top_card:
            raise ValueError("Top card is null")

        card_label = GameUi.get_card_label(top_card)
        await self.message.edit(components=[],
                                content=f"🏆 {member.mention} has won the game!\n\n... by placing {card_label} as their last card.",
                                files=[])

        await asyncio.sleep(30)
        await self.message.delete()
        self.reset_game()

    async def handle_color_selection(self, interaction: discord.Interaction, card_id: int, color: str) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        player_cards = self.game_logic.get_player_cards(str(member.id))
        card = next((c for c in player_cards if c["id"] == card_id), None)

        if not card:
            await interaction.response.send_message(content="Card not found.", ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result2 = self.game_logic.play_card(str(member.id), card_id)
        if hasattr(result2, "error") and result2.error:
            await interaction.response.send_message(content=result2.error, ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result1 = self.game_logic.change_wild_card_color(card_id, color)
        if hasattr(result1, "error") and result1.error:
            await interaction.response.send_message(content=result1.error, ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        self.last_player = member

        await interaction.response.send_message(content="You played a card.", ephemeral=True)

        await interaction.delete_original_response()

        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], str(member.id))

        top_card = self.game_logic.get_top_card()

        embed = self.get_game_message_content()
        files = [File(GameUi.get_card_image_path(top_card))] if top_card else []

        await self.message.edit(embeds=[embed], files=files)

        is_winner = self.game_logic.is_winner(str(member.id))
        if not is_winner:
            return

        if not top_card:
            raise ValueError("Top card is null")

        card_label = GameUi.get_card_label(top_card)
        await self.message.edit(components=[],
                                content=f"🏆 {member.mention} has won the game!\n\n... by placing {card_label} as their last card.",
                                files=[])

        await asyncio.sleep(30)
        await self.message.delete()
        self.reset_game()

    async def handle_draw_card_button(self, interaction: discord.Interaction) -> None:
        print("ass")
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user
        current_player = self.game_logic.get_current_player()

        if current_player["id"] != str(member.id):
            await interaction.response.send_message(content="It is not your turn.", ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result = self.game_logic.draw_card(str(member.id))
        if hasattr(result, "error") and result.error:
            await interaction.response.send_message(content=result.error, ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await interaction.response.send_message(content="You drew a card.", ephemeral=True)

        await interaction.delete_original_response()

        await self.delete_action_replies(["cardSelection", "wildCardColorSelection"], str(member.id))

        await self.message.edit(embeds=[self.get_game_message_content()])

    async def handle_say_uno(self, interaction: discord.Interaction) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user

        if str(member.id) != self.game_logic.get_current_player()["id"]:
            await interaction.response.send_message(content="It is not your turn.", ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        result = self.game_logic.say_uno(str(member.id))

        if hasattr(result, "error") and result.error:
            await interaction.response.send_message(content=result.error, ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await interaction.response.send_message(content=f"{member.mention} said UNO!")

        await asyncio.sleep(10)
        await interaction.delete_original_response()

    async def handle_cheat_code(self, interaction: discord.Interaction, code: str) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        member = interaction.user

        result = error("No cheat code found")
        if code == "gw4":
            result = self.game_logic.activate_cheat_code(str(member.id), GameCheat.GIVE_WILD_FOUR)
        elif code == "gw8":
            result = self.game_logic.activate_cheat_code(str(member.id), GameCheat.GIVE_WILD_EIGHT)

        if hasattr(result, "error") and result.error:
            await interaction.response.send_message(content=result.error, ephemeral=True)

            await asyncio.sleep(10)
            await interaction.delete_original_response()
            return

        await self.message.edit(embeds=[self.get_game_message_content()])

        await interaction.response.send_message(content="Cheat code activated.", ephemeral=True)

    async def handle_wild_card_color(self, card_id: int, interaction: discord.Interaction) -> None:
        colors = ["Red", "Green", "Blue", "Yellow"]

        view = ui.View()
        for color in colors:
            color_emoji = GameUi.get_color_emoji(color)
            button = ui.Button(label=color_emoji, style=ButtonStyle.secondary, custom_id=f"color-{color}-{card_id}")
            view.add_item(button)

        await interaction.response.send_message(content="Select a color for the wild card:", view=view, ephemeral=True)

        member = interaction.user
        await self.delete_action_replies(["wildCardColorSelection"], str(member.id))
        self.add_action_player_interaction("wildCardColorSelection", str(member.id), interaction)

    def add_action_player_interaction(self, action: str, player_id: str, interaction: discord.Interaction) -> None:
        if player_id not in self.action_player_interactions[action]:
            self.action_player_interactions[action][player_id] = []
        self.action_player_interactions[action][player_id].append(interaction)

    async def delete_action_replies(self, actions: List[str], player_id: str) -> None:
        for action in actions:
            if player_id in self.action_player_interactions.get(action, {}):
                interactions = self.action_player_interactions[action][player_id].copy()
                self.action_player_interactions[action][player_id] = []
                for reply in interactions:
                    try:
                        await reply.delete_original_response()
                    except:
                        pass

    def reset_game(self) -> None:
        self.initiator = None
        self.message = None
        self.players.clear()
        self.game_logic.reset()

    async def start_game(self) -> None:
        if self.message is None:
            raise ValueError("Message is null")

        player_ids = [str(player.id) for player in self.players]
        self.game_logic.start_game(player_ids)

        id_order = [player["id"] for player in self.game_logic.get_players()]
        self.players.sort(key=lambda player: id_order.index(str(player.id)))

        # Use the UnoButtonView class instead of creating generic buttons
        view = UnoButtonView(self)

        await self.message.edit(
            view=view,
            content=None,
            embeds=[self.get_game_message_content()]
        )

    def get_game_message_content(self) -> discord.Embed:
        players = []
        for player in self.players:
            card_count = len(self.game_logic.get_player_cards(str(player.id)))
            if str(player.id) == self.game_logic.get_current_player()["id"]:
                players.append(f"> {player.mention} ({card_count} cards)")
            else:
                players.append(f"     {player.mention} ({card_count} cards)")

        if self.game_logic.is_reversed():
            players.reverse()

        order_message = "\n".join(players)

        top_card = self.game_logic.get_top_card()
        top_card_label = GameUi.get_card_label(top_card) if top_card else "None"

        deck_card_amount = len(self.game_logic.get_deck_cards())
        discard_card_amount = len(self.game_logic.get_discard_cards())

        embed = discord.Embed(title="UNO Game Status", color=discord.Color.red())

        embed.add_field(name="Deck", value=str(deck_card_amount), inline=True)
        embed.add_field(name="Discard", value=str(discard_card_amount), inline=True)
        embed.add_field(name="Players", value=order_message, inline=False)
        embed.add_field(name="Top card", value=top_card_label, inline=True)
        embed.add_field(name="Placed by", value=self.last_player.mention if self.last_player else "None", inline=True)

        if top_card:
            path = GameUi.get_card_image_path(top_card)
            length = len("./assets/images/cards/")
            embed.set_image(url=f"attachment://{path[length:]}")

        return embed

    def get_message_content(self) -> str:
        if self.initiator is None:
            raise ValueError("Initiator is null")

        player_mentions = ", ".join(player.mention for player in self.players)
        return f"{self.initiator.mention} has created an UNO lobby.\n\nPlayers: {player_mentions}"
