import re

import discord
from discord.ext import commands

from commands.game_ui import GameUi, GameView, UnoButtonView

from dotenv import dotenv_values

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

game_ui = GameUi()


@bot.event
async def on_ready():
    global game_view
    game_view = GameView(game_ui)
    bot.add_view(game_view)
    uno_view = UnoButtonView(game_ui)
    bot.add_view(uno_view)
    print(f"Bot is ready as {bot.user}")
    print(f"Registered commands: {[cmd.name for cmd in bot.application_commands]}")


@bot.command(name="uno")
async def start(ctx):
    print("UNO command received from", ctx.author)
    await game_ui.handle_start(ctx)


@bot.event
async def on_application_command_error(ctx, error):
    print(f"Command error: {error}")
    import traceback
    traceback.print_exception(type(error), error, error.__traceback__)


# Handle custom interactions for card buttons
@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Only handle component interactions and skip command interactions
    if interaction.type != discord.InteractionType.component:
        return

    # Skip if this is a command interaction
    if hasattr(interaction, 'command') and interaction.command is not None:
        return

    custom_id = interaction.data.get("custom_id", "")

    # Handle card button
    card_match = re.match(r'^card-(\d+)$', custom_id)
    if card_match:
        card_id = int(card_match.group(1))
        await game_ui.handle_card_button(interaction, card_id)
        return

    # Handle color button
    color_match = re.match(r'^color-(Red|Green|Blue|Yellow)-(\d+)$', custom_id)
    if color_match:
        color = color_match.group(1)
        card_id = int(color_match.group(2))
        await game_ui.handle_color_selection(interaction, card_id, color)
        return


if __name__ == "__main__":
    config = dotenv_values(".env")
    token = config.get("TOKEN")
    if token is None or not token:
        raise ValueError("loo fail nimega .env ja pane sinna TOKEN=isiklik Discord Developer Portal token")
    bot.run(token)
