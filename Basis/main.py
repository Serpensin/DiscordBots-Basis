#Import
import asyncio
import discord
import json
import logging
import logging.handlers
import os
import platform
import sys
import time
from datetime import timedelta
from dotenv import load_dotenv
from zipfile import ZIP_DEFLATED, ZipFile



#Init
app_folder_name = 'BOTFOLDER'
bot_name = 'BOTNAME'
if not os.path.exists(f'{app_folder_name}//Logs'):
    os.makedirs(f'{app_folder_name}//Logs')
if not os.path.exists(f'{app_folder_name}//Buffer'):
    os.makedirs(f'{app_folder_name}//Buffer')
log_folder = f'{app_folder_name}//Logs//'
buffer_folder = f'{app_folder_name}//Buffer//'
logger = logging.getLogger('discord')
manlogger = logging.getLogger('Program')
logger.setLevel(logging.INFO)
manlogger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename = f'{log_folder}{bot_name}.log',
    encoding = 'utf-8',
    maxBytes = 8 * 1024 * 1024, 
    backupCount = 5,            
    mode='w')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
manlogger.addHandler(handler)
manlogger.info('Engine powering up...')

#Load env
load_dotenv()
TOKEN = os.getenv('TOKEN')
ownerID = os.getenv('OWNER_ID')


class aclient(discord.AutoShardedClient):
    def __init__(self):

        intents = discord.Intents.default()
        intents.guild_messages = True
        intents.dm_messages = True
        intents.members = True

        super().__init__(owner_id = ownerID,
                              intents = intents,
                              status = discord.Status.invisible
                        )
        self.synced = False


    class Presence():
        @staticmethod
        def get_activity() -> discord.Activity:
            with open('activity.json') as f:
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
            with open('activity.json') as f:
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


    async def on_ready(self):
        global owner
        try:
            owner = await self.fetch_user(ownerID)
            if owner is None:
                manlogger.critical(f"Invalid ownerID: {ownerID}")
                sys.exit(f"Invalid ownerID: {ownerID}")
        except discord.HTTPException as e:
            manlogger.critical(f"Error fetching owner user: {e}")
            sys.exit(f"Error fetching owner user: {e}")
        logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            manlogger.info('Syncing...')
            await tree.sync()
            manlogger.info('Synced.')
            self.synced = True
            await bot.change_presence(activity = self.Presence.get_activity(), status = self.Presence.get_status())
        manlogger.info('All systems online...')
        print('READY')
bot = aclient()
tree = discord.app_commands.CommandTree(bot)


# Check if all required variables are set
owner_available = bool(ownerID)

#Fix error on windows on shutdown
if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
def clear():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

##Events
class Events():
    @bot.event
    async def on_guild_remove(guild):
        manlogger.info(f'I got kicked from {guild}. (ID: {guild.id})')
    
    @bot.event
    async def on_guild_join(guild):
        manlogger.info(f'I joined {guild}. (ID: {guild.id})')
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                perms = []
                for roles in guild.roles:
                    if roles.permissions.manage_guild and roles.permissions.manage_roles or roles.permissions.administrator and not roles.is_bot_managed():
                        perms.append(roles.id)
                if perms == []:
                    break
                else:
                    for role in perms: 
                        await channel.send(f'<@&{role}>')
                    await channel.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the translation setup.')
                return
        for member in guild.members:
            if str(member.status) != 'offline' and member != guild.owner and not member.bot:
                if any((role.permissions.manage_guild and role.permissions.manage_roles) or (role.permissions.administrator and not role.is_bot_managed()) for role in member.roles):
                    try:
                        await member.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the translation setup.')
                        return
                    except discord.Forbidden:
                        continue
        try:
            await guild.owner.send('Hello! I\'m DBDStats, a bot for Dead by Daylight stats. Please use /setup_help to get help with the translation setup.')
        except discord.Forbidden:
            manlogger.info(f'Failed to send setup message for {guild}.')
    
    @tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
        options = interaction.data.get("options")
        option_values = ""
        if options:
            for option in options:
                option_values += f"{option['name']}: {option['value']}"
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            await interaction.response.send_message(f'This command is on cooldown.\nTime left: `{await Functions.seconds_to_minutes(error.retry_after)}`.', ephemeral=True)
        else:
            try:
                await interaction.followup.send(f"{error}\n\n{option_values}", ephemeral=True)
            except:
                await interaction.response.send_message(f"{error}\n\n{option_values}", ephemeral=True)
            manlogger.warning(f"{error} -> {option_values} | Invoked by {interaction.user.name} ({interaction.user.id})")


#Functions
def seconds_to_minutes(input_int):
    return(str(timedelta(seconds=input_int)))

 
##Owner Commands
#Shutdown
@tree.command(name = 'shutdown', description = 'Savely shut down the bot.')
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        manlogger.info('Engine powering down...')
        await bot.change_presence(status = discord.Status.invisible)
        await interaction.response.send_message('Engine powering down...', ephemeral = True)
        await bot.close()
    else:
        await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)


#Get Logs
if owner_available:
    @tree.command(name = 'get_logs', description = 'Get the current, or all logfiles.')
    @discord.app_commands.describe(choice = 'Choose which log files you want to receive.')
    @discord.app_commands.choices(choice = [
        discord.app_commands.Choice(name="Last X lines", value="xlines"),
        discord.app_commands.Choice(name="Current Log", value="current"),
        discord.app_commands.Choice(name="Whole Folder", value="whole")
    ])
    async def self(interaction: discord.Interaction, choice: str):
        if interaction.user.id != int(ownerID):
            await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)
            return
        else:
            if choice == 'xlines':
                class LastXLines(discord.ui.Modal, title = 'Line Input'):
                    def __init__(self, interaction):
                        super().__init__()
                        self.timeout = 15
                        self.answer = discord.ui.TextInput(label = 'How many lines?', style = discord.TextStyle.short, required = True, min_length = 1, max_length = 4)
                        self.add_item(self.answer)

                    async def on_submit(self, interaction: discord.Interaction):
                        try:
                            int(self.answer.value)
                        except:
                            await interaction.response.send_message(content = 'You can only use numbers!', ephemeral = True)
                            return
                        if int(self.answer.value) == 0:
                            await interaction.response.send_message(content = 'You can not use 0 as a number!', ephemeral = True)
                            return
                        with open(f'{log_folder}{bot_name}.log', 'r', encoding='utf8') as f:
                            with open(buffer_folder+'log-lines.txt', 'w', encoding='utf8') as f2:
                                count = 0
                                for line in (f.readlines()[-int(self.answer.value):]):
                                    f2.write(line)
                                    count += 1
                        await interaction.response.send_message(content = f'Here are the last {count} lines of the current logfile:', file = discord.File(r''+buffer_folder+'log-lines.txt') , ephemeral = True)
                        if os.path.exists(buffer_folder+'log-lines.txt'):
                            os.remove(buffer_folder+'log-lines.txt')
                await interaction.response.send_modal(LastXLines(interaction))
            elif choice == 'current':
                await interaction.response.defer(ephemeral = True)
                try:
                    await interaction.followup.send(file=discord.File(r''f'{log_folder}{bot_name}.log'), ephemeral=True)
                except discord.HTTPException as err:
                    if err.status == 413:
                        with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                            f.write(f'{log_folder}{bot_name}.log')
                        try:
                            await interaction.response.send_message(file=discord.File(r''+buffer_folder+'Logs.zip'))
                        except discord.HTTPException as err:
                            if err.status == 413:
                                await interaction.followup.send("The log is too big to be send directly.\nYou have to look at the log in your server(VPS).")
                        os.remove(buffer_folder+'Logs.zip')
            elif choice == 'whole':
                if os.path.exists(buffer_folder+'Logs.zip'):
                    os.remove(buffer_folder+'Logs.zip')
                with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                    for file in os.listdir(log_folder):
                        if file.endswith(".zip"):
                            continue
                        f.write(log_folder+file)
                try:
                    await interaction.response.send_message(file=discord.File(r''+buffer_folder+'Logs.zip'), ephemeral=True)
                except discord.HTTPException as err:
                    if err.status == 413:
                        await interaction.followup.send("The folder is too big to be send directly.\nPlease get the current file, or the last X lines.")
                os.remove(buffer_folder+'Logs.zip')


#Change Activity
if owner_available:
    @tree.command(name = 'activity', description = 'Change my activity.')
    @discord.app_commands.describe(type='The type of Activity you want to set.', title='What you want the bot to play, stream, etc...', url='Url of the stream. Only used if activity set to \'streaming\'.')
    @discord.app_commands.choices(type=[
        discord.app_commands.Choice(name='Competing', value='Competing'),
        discord.app_commands.Choice(name='Listening', value='Listening'),
        discord.app_commands.Choice(name='Playing', value='Playing'),
        discord.app_commands.Choice(name='Streaming', value='Streaming'),
        discord.app_commands.Choice(name='Watching', value='Watching')
        ])
    async def self(interaction: discord.Interaction, type: str, title: str, url: str = ''):
        if interaction.user.id == int(ownerID):
            await interaction.response.defer(ephemeral = True)
            with open('activity.json') as f:
                data = json.load(f)
            if type == 'Playing':
                data['activity_type'] = 'Playing'
                data['activity_title'] = title
            elif type == 'Streaming':
                data['activity_type'] = 'Streaming'
                data['activity_title'] = title
                data['activity_url'] = url
            elif type == 'Listening':
                data['activity_type'] = 'Listening'
                data['activity_title'] = title
            elif type == 'Watching':
                data['activity_type'] = 'Watching'
                data['activity_title'] = title
            elif type == 'Competing':
                data['activity_type'] = 'Competing'
                data['activity_title'] = title
            with open('activity.json', 'w', encoding='utf8') as f:
                json.dump(data, f, indent=2)
            await bot.change_presence(activity = bot.Presence.get_activity(), status = bot.Presence.get_status())
            await interaction.followup.send('Activity changed!', ephemeral = True)
        else:
            await interaction.followup.send('Only the BotOwner can use this command!', ephemeral = True)


#Change Status
@tree.command(name = 'status', description = 'Change my status.')
@discord.app_commands.describe(status='The status you want to set.')
@discord.app_commands.choices(status=[
    discord.app_commands.Choice(name='Online', value='online'),
    discord.app_commands.Choice(name='Idle', value='idle'),
    discord.app_commands.Choice(name='Do not disturb', value='dnd'),
    discord.app_commands.Choice(name='Invisible', value='invisible')
    ])
async def self(interaction: discord.Interaction, status: str):
    if interaction.user.id == int(ownerID):
        await interaction.response.defer(ephemeral = True)
        with open('activity.json') as f:
            data = json.load(f)
        data['status'] = status
        with open('activity.json', 'w', encoding='utf8') as f:
            json.dump(data, f, indent=2)
        await bot.change_presence(activity = bot.get_activity(), status = bot.get_status())
        await interaction.followup.send('Status changed!', ephemeral = True)
    else:
        await interaction.followup.send('Only the BotOwner can use this command!', ephemeral = True)



##Bot Commands
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
@discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.user.id))
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! \nCommand execution time: `{int(ping)}ms`\nPing to gateway: `{int(bot.latency * 1000)}ms`')


#Change Nickname
@tree.command(name = 'change_nickname', description = 'Change the nickname of the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_nicknames = True)
@discord.app_commands.describe(nick='New nickname for me.')
async def self(interaction: discord.Interaction, nick: str):
    await interaction.guild.me.edit(nick=nick)
    await interaction.response.send_message(f'My new nickname is now **{nick}**.', ephemeral=True)






if __name__ == '__main__':
    try:
        bot.run(TOKEN, log_handler=None)
    except discord.errors.LoginFailure:
        manlogger.critical('TOKEN is not set.')
        sys.exit('TOKEN is not set.')

