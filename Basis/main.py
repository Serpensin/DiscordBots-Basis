﻿#Import
import time
startupTime_start = time.time()
import asyncio
import datetime
import discord
import json
import jsonschema
import os
import platform
import psutil
import sentry_sdk
import signal
import sys
from aiohttp import web
from CustomModules.app_translation import Translator as CustomTranslator
from CustomModules import log_handler
from dotenv import load_dotenv
from typing import Optional, Any
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile



#Init
discord.VoiceClient.warn_nacl = False # Delete this line if you want to use voice
APP_FOLDER_NAME = 'BOTFOLDER'
BOT_NAME = 'BOTNAME'
os.makedirs(f'{APP_FOLDER_NAME}//Logs', exist_ok=True)
os.makedirs(f'{APP_FOLDER_NAME}//Buffer', exist_ok=True)
LOG_FOLDER = f'{APP_FOLDER_NAME}//Logs//'
BUFFER_FOLDER = f'{APP_FOLDER_NAME}//Buffer//'
ACTIVITY_FILE = f'{APP_FOLDER_NAME}//activity.json'
BOT_VERSION = "1.0.0"
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    environment='Production',
    release=f'{BOT_NAME}@{BOT_VERSION}'
)

#Load env
load_dotenv()
TOKEN = os.getenv('TOKEN')
OWNERID = os.getenv('OWNER_ID')
LOG_LEVEL = os.getenv('LOG_LEVEL')
SUPPORTID = os.getenv('SUPPORT_SERVER')

#Logger init
log_manager = log_handler.LogManager(LOG_FOLDER, BOT_NAME, LOG_LEVEL)
discord_logger = log_manager.get_logger('discord')
program_logger = log_manager.get_logger('Program')
program_logger.info('Engine powering up...')

#Create activity.json if not exists
class JSONValidator:
    schema = {
        "type" : "object",
        "properties" : {
            "activity_type" : {
                "type" : "string",
                "enum" : ["Playing", "Streaming", "Listening", "Watching", "Competing"]
            },
            "activity_title" : {"type" : "string"},
            "activity_url" : {"type" : "string"},
            "status" : {
                "type" : "string",
                "enum" : ["online", "idle", "dnd", "invisible"]
            },
        },
    }

    default_content = {
        "activity_type": "Playing",
        "activity_title": "Made by Serpensin: https://github.com/Serpensin",
        "activity_url": "",
        "status": "online"
    }

    def __init__(self, file_path):
        self.file_path = file_path

    def validate_and_fix_json(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                    jsonschema.validate(instance=data, schema=self.schema)  # validate the data
                except (jsonschema.exceptions.ValidationError, json.decoder.JSONDecodeError) as e:
                    program_logger.error(f'ValidationError: {e}')
                    self.write_default_content()
        else:
            self.write_default_content()

    def write_default_content(self):
        with open(self.file_path, 'w', encoding='utf-8') as file:
            json.dump(self.default_content, file, indent=4)
JSONValidator(ACTIVITY_FILE).validate_and_fix_json()


class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()
        #intents.guild_messages = True
        #intents.members = True

        super().__init__(owner_id = OWNERID,
                              intents = intents,
                              status = discord.Status.invisible,
                              auto_reconnect = True
                        )
        self.synced = False
        self.initialized = False


    class Presence():
        @staticmethod
        def get_activity() -> discord.Activity:
            with open(ACTIVITY_FILE) as f:
                data = json.load(f)
                activity_type = data['activity_type']
                activity_title = data['activity_title']
                activity_url = data['activity_url']
            if activity_type == 'Playing':
                return discord.Game(name=activity_title)
            elif activity_type == 'Streaming':
                return discord.Streaming(name=activity_title, url=activity_url)
            elif activity_type == 'Listening':
                return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
            elif activity_type == 'Watching':
                return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
            elif activity_type == 'Competing':
                return discord.Activity(type=discord.ActivityType.competing, name=activity_title)

        @staticmethod
        def get_status() -> discord.Status:
            with open(ACTIVITY_FILE) as f:
                data = json.load(f)
                status = data['status']
            if status == 'online':
                return discord.Status.online
            elif status == 'idle':
                return discord.Status.idle
            elif status == 'dnd':
                return discord.Status.dnd
            elif status == 'invisible':
                return discord.Status.invisible


    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        options = interaction.data.get("options")
        option_values = ""
        if options:
            for option in options:
                option_values += f"{option['name']}: {option['value']}"

        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown.\nTime left: `{str(datetime.timedelta(seconds=int(error.retry_after)))}`',
                ephemeral=True
            )
        elif isinstance(error, discord.app_commands.MissingPermissions):
            missing_permissions = [perm.replace("_", " ").capitalize() for perm in error.missing_permissions]
            await interaction.response.send_message(
                f"You are missing the following permissions to execute this command: {', '.join(missing_permissions)}",
                ephemeral=True
            )
        else:
            try:
                try:
                    await interaction.response.send_message("Error! Try again.", ephemeral=True)
                except:
                    try:
                        await interaction.followup.send("Error! Try again.", ephemeral=True)
                    except:
                        pass
            except discord.Forbidden:
                missing_permissions = []
                bot_member = interaction.guild.me
                if bot_member:
                    for perm, value in bot_member.guild_permissions:
                        if not value:
                            missing_permissions.append(perm.replace("_", " ").capitalize())

                missing_text = (
                    f"I am missing the following permissions: {', '.join(missing_permissions)}"
                    if missing_permissions
                    else "I am missing required permissions."
                )

                try:
                    await interaction.followup.send(
                        f"{error}\n\n{missing_text}\n\n{option_values}",
                        ephemeral=True
                    )
                except discord.NotFound:
                    try:
                        await interaction.response.send_message(
                            f"{error}\n\n{missing_text}\n\n{option_values}",
                            ephemeral=True
                        )
                    except discord.NotFound:
                        pass
                except Exception as e:
                    discord_logger.warning(f"Unexpected error while sending message: {e}")
            finally:
                try:
                    program_logger.warning(
                        f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) @ {interaction.guild.name} ({interaction.guild.id}) with Language {interaction.locale[1]}"
                    )
                except AttributeError:
                    program_logger.warning(
                        f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id}) with Language {interaction.locale[1]}"
                    )
                sentry_sdk.capture_exception(error)

    async def on_guild_join(self, guild):
        if not self.synced:
            return
        discord_logger.info(f'I joined {guild}. (ID: {guild.id})')

    async def on_message(self, message):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'Commands:\n'
                                       'help - Shows this message\n'
                                       'log - Get the log\n'
                                       'activity - Set the activity of the bot\n'
                                       'status - Set the status of the bot\n'
                                       'shutdown - Shutdown the bot\n'
                                       '```')

        if message.guild is None and message.author.id == int(OWNERID):
            args = message.content.split(' ')
            program_logger.debug(args)
            command, *args = args
            match command:
                case 'help':
                    await __wrong_selection()
                    return
                case 'log':
                    await Owner.log(message, args)
                    return
                case 'activity':
                    await Owner.activity(message, args)
                    return
                case 'status':
                    await Owner.status(message, args)
                    return
                case 'shutdown':
                    await Owner.shutdown(message)
                    return
                case _:
                    await __wrong_selection()

    async def on_guild_remove(self, guild):
        if not self.synced:
            return
        program_logger.info(f'I got kicked from {guild}. (ID: {guild.id})')

    async def setup_hook(self):
        global owner, shutdown
        shutdown = False
        try:
            owner = await self.fetch_user(OWNERID)
            if owner is None:
                program_logger.critical(f"Invalid ownerID: {OWNERID}")
                sys.exit(f"Invalid ownerID: {OWNERID}")
        except discord.HTTPException as e:
            program_logger.critical(f"Error fetching owner user: {e}")
            sys.exit(f"Error fetching owner user: {e}")
        discord_logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        discord_logger.info('Syncing...')
        await tree.set_translator(CustomTranslator())
        await tree.sync()
        discord_logger.info('Synced.')
        self.synced = True

    async def on_ready(self):
        await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
        if self.initialized:
            return
        bot.loop.create_task(Tasks.health_server())
        global start_time
        start_time = datetime.datetime.now(datetime.UTC)
        program_logger.info(f"Initialization completed in {time.time() - startupTime_start} seconds.")
        self.initialized = True
        
bot = aclient()
tree = discord.app_commands.CommandTree(bot)
tree.on_error = bot.on_app_command_error


#Load Modules
from CustomModules import context_commands, nickname
context_commands.setup(tree)
nickname.setup(bot, tree, program_logger)



class Tasks():
    async def health_server():
        async def __health_check(request):
            return web.Response(text="Healthy")

        app = web.Application()
        app.router.add_get('/health', __health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 5000)
        try:
            await site.start()
        except OSError as e:
            program_logger.warning(f'Error while starting health server: {e}')
            program_logger.debug(f'Error while starting health server: {e}')


class SignalHandler:
    def __init__(self):
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        program_logger.info('Received signal to shutdown...')
        bot.loop.create_task(Owner.shutdown(owner))



#Fix error on windows on shutdown
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())



#Functions
class Functions():
    def format_seconds(seconds):
        """
        Converts a given number of seconds into a human-readable string format.

        :param seconds: The total number of seconds to be converted.
        :return: A string representing the time in years, days, hours, minutes, and seconds.
        """
        years, remainder = divmod(seconds, 31536000)
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if years:
            parts.append(f"{years}y")
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        if seconds:
            parts.append(f"{seconds}s")

        return " ".join(parts)

    async def get_or_fetch(item: str, item_id: int) -> Optional[Any]:
        """
        Attempts to retrieve an object using the 'get_<item>' method of the bot class, and
        if not found, attempts to retrieve it using the 'fetch_<item>' method.

        :param item: Name of the object to retrieve
        :param item_id: ID of the object to retrieve
        :return: Object if found, else None
        :raises AttributeError: If the required methods are not found in the bot class
        """
        get_method_name = f'get_{item}'
        fetch_method_name = f'fetch_{item}'

        get_method = getattr(bot, get_method_name, None)
        fetch_method = getattr(bot, fetch_method_name, None)

        if get_method is None or fetch_method is None:
            raise AttributeError(f"Methods {get_method_name} or {fetch_method_name} not found on bot object.")

        item_object = get_method(item_id)
        if item_object is None:
            try:
                item_object = await fetch_method(item_id)
            except discord.NotFound:
                pass
        return item_object

    async def create_support_invite(interaction):
        """
        Creates a one-time use invite link to the support guild for the user who invoked the command.

        :param interaction: The interaction that triggered the command.
        :return: A string containing the invite URL or an error message if the invite could not be created.
        """
        try:
            guild = bot.get_guild(int(SUPPORTID))
        except ValueError:
            return "Could not find support guild."
        if guild is None:
            return "Could not find support guild."
        if not guild.text_channels:
            return "Support guild has no text channels."
        try:
            member = await guild.fetch_member(interaction.user.id)
        except discord.NotFound:
            member = None
        if member is not None:
            return "You are already in the support guild."
        channels: discord.TextChannel = guild.text_channels
        for channel in channels:
            try:
                invite: discord.Invite = await channel.create_invite(
                    reason=f"Created invite for {interaction.user.name}" + (f" from server {interaction.guild.name} ({interaction.guild_id})" if interaction.guild and interaction.guild.name else ""),
                    max_age=60,
                    max_uses=1,
                    unique=True
                )
                return invite.url
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue
        return "Could not create invite. There is either no text-channel, or I don't have the rights to create an invite."



##Owner Commands
class Owner():
    async def log(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'log [current/folder/lines] (Replace lines with a positive number, if you only want lines.) - Get the log\n'
                                       '```')
        if not args:
            await __wrong_selection()
            return

        command = args[0]
        if command == 'current':
            log_file_path = f'{LOG_FOLDER}{BOT_NAME}.log'
            try:
                await message.channel.send(file=discord.File(log_file_path))
            except discord.HTTPException as err:
                if err.status == 413:
                    zip_path = f'{BUFFER_FOLDER}Logs.zip'
                    with ZipFile(zip_path, mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as zip_file:
                        zip_file.write(log_file_path)
                    try:
                        await message.channel.send(file=discord.File(zip_path))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await message.channel.send("The log is too big to be sent directly.\nYou have to look at the log in your server (VPS).")
                    os.remove(zip_path)
            return

        if command == 'folder':
            zip_path = f'{BUFFER_FOLDER}Logs.zip'
            if os.path.exists(zip_path):
                os.remove(zip_path)
            with ZipFile(zip_path, mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as zip_file:
                for file in os.listdir(LOG_FOLDER):
                    if not file.endswith(".zip"):
                        zip_file.write(f'{LOG_FOLDER}{file}')
            try:
                await message.channel.send(file=discord.File(zip_path))
            except discord.HTTPException as err:
                if err.status == 413:
                    await message.channel.send("The folder is too big to be sent directly.\nPlease get the current file or the last X lines.")
            os.remove(zip_path)
            return

        try:
            lines = int(command)
            if lines < 1:
                await __wrong_selection()
                return
        except ValueError:
            await __wrong_selection()
            return

        log_file_path = f'{LOG_FOLDER}{BOT_NAME}.log'
        buffer_file_path = f'{BUFFER_FOLDER}log-lines.txt'
        with open(log_file_path, 'r', encoding='utf8') as log_file:
            log_lines = log_file.readlines()[-lines:]
        with open(buffer_file_path, 'w', encoding='utf8') as buffer_file:
            buffer_file.writelines(log_lines)
        await message.channel.send(content=f'Here are the last {len(log_lines)} lines of the current logfile:', file=discord.File(buffer_file_path))
        os.remove(buffer_file_path)

    async def activity(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'activity [playing/streaming/listening/watching/competing] [title] (url) - Set the activity of the bot\n'
                                       '```')
        def isURL(zeichenkette):
            try:
                ergebnis = urlparse(zeichenkette)
                return all([ergebnis.scheme, ergebnis.netloc])
            except:
                return False

        def remove_and_save(liste):
            if liste and isURL(liste[-1]):
                return liste.pop()
            else:
                return None

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        url = remove_and_save(args[1:])
        title = ' '.join(args[1:])
        program_logger.debug(title)
        program_logger.debug(url)
        with open(ACTIVITY_FILE, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'playing':
            data['activity_type'] = 'Playing'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'streaming':
            data['activity_type'] = 'Streaming'
            data['activity_title'] = title
            data['activity_url'] = url
        elif action == 'listening':
            data['activity_type'] = 'Listening'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'watching':
            data['activity_type'] = 'Watching'
            data['activity_title'] = title
            data['activity_url'] = ''
        elif action == 'competing':
            data['activity_type'] = 'Competing'
            data['activity_title'] = title
            data['activity_url'] = ''
        else:
            await __wrong_selection()
            return
        with open(ACTIVITY_FILE, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Activity set to {action} {title}{" " + url if url else ""}.')

    async def status(message, args):
        async def __wrong_selection():
            await message.channel.send('```'
                                       'status [online/idle/dnd/invisible] - Set the status of the bot\n'
                                       '```')

        if args == []:
            await __wrong_selection()
            return
        action = args[0].lower()
        with open(ACTIVITY_FILE, 'r', encoding='utf8') as f:
            data = json.load(f)
        if action == 'online':
            data['status'] = 'online'
        elif action == 'idle':
            data['status'] = 'idle'
        elif action == 'dnd':
            data['status'] = 'dnd'
        elif action == 'invisible':
            data['status'] = 'invisible'
        else:
            await __wrong_selection()
            return
        with open(ACTIVITY_FILE, 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
        await message.channel.send(f'Status set to {action}.')

    async def shutdown(message):
        """
        Shuts down the bot gracefully.

        This function sends a shutdown message, changes the bot's status to invisible,
        cancels all running tasks, and closes the bot connection.

        :param message: The message object that triggered the shutdown command.
        """
        global shutdown
        _message = 'Engine powering down...'
        program_logger.info(_message)
        try:
            await message.channel.send(_message)
        except:
            await owner.send(_message)
        await bot.change_presence(status=discord.Status.invisible)
        shutdown = True

        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        await bot.close()



##Bot Commands
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    """
    Responds with 'Pong!' and measures the command execution time and ping to the gateway.

    This function is an asynchronous command handler that responds to the 'ping' command.
    It sends a 'Pong!' message, measures the time taken to execute the command, and then
    edits the original response to include the command execution time and the ping to the gateway.

    :param interaction: The interaction that triggered the command.
    """
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! \nCommand execution time: `{int(ping)}ms`\nPing to gateway: `{int(bot.latency * 1000)}ms`')


#Bot Info
@tree.command(name = 'botinfo', description = 'Get information about the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    """
    Handles the 'botinfo' command to provide information about the bot.

    This function creates an embed message containing various details about the bot,
    such as its creation date, version, uptime, owner, server count, member count,
    shard information, and versions of Python, discord.py, and Sentry. If the user
    invoking the command is the bot owner, additional information about CPU and RAM
    usage is included.

    :param interaction: The interaction that triggered the command.
    """
    member_count = sum(guild.member_count for guild in bot.guilds)

    embed = discord.Embed(
        title=f"Information about {bot.user.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else '')

    embed_fields = [
        ("Created at", bot.user.created_at.strftime("%d.%m.%Y, %H:%M:%S"), True),
        ("Bot-Version", BOT_VERSION, True),
        ("Uptime", str(datetime.timedelta(seconds=int((datetime.datetime.now(datetime.UTC) - start_time).total_seconds()))), True),
        ("Bot-Owner", f"<@!{OWNERID}>", True),
        ("\u200b", "\u200b", True),
        ("\u200b", "\u200b", True),
        ("Server", f"{len(bot.guilds)}", True),
        ("Member count", str(member_count), True),
        ("\u200b", "\u200b", True),
        ("Shards", f"{bot.shard_count}", True),
        ("Shard ID", f"{interaction.guild.shard_id if interaction.guild else 'N/A'}", True),
        ("\u200b", "\u200b", True),
        ("Python-Version", platform.python_version(), True),
        ("discord.py-Version", discord.__version__, True),
        ("Sentry-Version", sentry_sdk.consts.VERSION, True),
        ("Repo", "[GitHub](https://github.com/Serpensin/DiscordBots-Basis)", True),
        ("Invite", f"[Invite me](https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot)", True),
        ("\u200b", "\u200b", True)
    ]

    if interaction.user.id == int(OWNERID):
        process = psutil.Process(os.getpid())
        cpu_usage = process.cpu_percent()
        ram_usage = round(process.memory_percent(), 2)
        ram_real = round(process.memory_info().rss / (1024 ** 2), 2)

        embed_fields.extend([
            ("CPU", f"{cpu_usage}%", True),
            ("RAM", f"{ram_usage}%", True),
            ("RAM", f"{ram_real} MB", True)
        ])

    for name, value, inline in embed_fields:
        embed.add_field(name=name, value=value, inline=inline)

    await interaction.response.send_message(embed=embed)


#Support Invite
@tree.command(name = 'support', description = 'Get invite to our support server.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.user.id))
async def support(interaction: discord.Interaction):
    """
    Handles the 'support' command to provide an invite to the support server.

    This function checks if the command was invoked in a guild. If not, it creates and sends
    an invite to the support server. If the command was invoked in a guild that is not the
    support server, it also creates and sends an invite. If the command was invoked in the
    support server, it informs the user that they are already in the support server.

    :param interaction: The interaction that triggered the command.
    """
    if not SUPPORTID:
        await interaction.response.send_message('There is no support server setup!', ephemeral=True)
        return
    if interaction.guild is None:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral=True)
        return
    if str(interaction.guild.id) != SUPPORTID:
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(await Functions.create_support_invite(interaction), ephemeral=True)
    else:
        await interaction.response.send_message('You are already in our support server!', ephemeral=True)





if __name__ == '__main__':
    if sys.version_info < (3, 11):
        program_logger.critical('Python 3.11 or higher is required.')
        sys.exit(1)
    if not TOKEN:
        program_logger.critical('Missing token. Please check your .env file.')
        sys.exit()
    else:
        SignalHandler()
        try:
            bot.run(TOKEN, log_handler=None)
        except discord.errors.LoginFailure:
            program_logger.critical('Invalid token. Please check your .env file.')
            sys.exit()
        except asyncio.CancelledError:
            if shutdown:
                pass
