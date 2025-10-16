from re import I
import discord
import logging

__name__ = "Nickname"

def setup(client: discord.Client, tree: discord.app_commands.CommandTree, logger: logging.Logger = None) -> None:
    """
    Sets up the Nickname module by registering the command and initializing the logger.

    This function ensures that the required client and command tree are provided,
    initializes the logger, and registers the 'change_nickname' command to the command tree.

    :param client: The Discord client instance.
    :param tree: The command tree to which commands are added.
    :param logger: (Optional) A logger instance for logging messages. If not provided, a default logger is used.
    :raises ValueError: If the client or command tree is None.
    """
    if not client:
        raise ValueError("Client is None")
    if not tree:
        raise ValueError("Command tree is None")

    global _bot, _logger
    _bot = client
    _logger = (logger or logging.getLogger("null")).getChild(__name__)
    _logger.addHandler(logging.NullHandler()) if logger is None else None

    tree.add_command(_change_nickname)
    _logger.info(f"Module {__name__} has been set up.")


# Change Nickname
@discord.app_commands.command(name='change_nickname', description='Change the nickname of the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_nicknames=True)
@discord.app_commands.describe(nick='New nickname for me.')
@discord.app_commands.guild_only()
async def _change_nickname(interaction: discord.Interaction, nick: str) -> None:
    """
    Handles the 'change_nickname' command to change the bot's nickname.

    This function edits the bot's nickname in the guild where the command was invoked
    and sends a confirmation message to the user.

    :param interaction: The interaction that triggered the command.
    :param nick: The new nickname to set for the bot.
    :raises discord.Forbidden: If the bot lacks permissions to change its nickname.
    :raises discord.HTTPException: If an error occurs while editing the nickname.
    """
    await interaction.response.defer(ephemeral=True)

    await interaction.guild.me.edit(nick=nick)
    await interaction.followup.send(f'My new nickname is now **{nick}**.', ephemeral=True)