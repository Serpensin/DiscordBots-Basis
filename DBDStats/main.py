#Import
import time
from zipfile import ZIP_DEFLATED, ZipFile
import discord
import logging
import logging.handlers
import os
import json
from datetime import timedelta
from dotenv import load_dotenv



#Init
if not os.path.exists('BOTFOLDER'):
    os.mkdir('BOTFOLDER')
if not os.path.exists('BOTFOLDER//Logs'):
    os.mkdir('BOTFOLDER//Logs')
if not os.path.exists('BOTFOLDER//Buffer'):
    os.mkdir('BOTFOLDER//Buffer')
log_folder = 'BOTFOLDER//Logs//'
buffer_folder = 'BOTFOLDER//Buffer//'
logger = logging.getLogger('discord')
manlogger = logging.getLogger('Program')
logger.setLevel(logging.INFO)
manlogger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler(
    filename = log_folder+'BotLog.log',
    encoding = 'utf-8',
    maxBytes = 8 * 1024 * 1024, 
    backupCount = 5,            
    mode='w')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)
manlogger.addHandler(handler)
manlogger.info('------')
manlogger.info('Engine powering up...')
load_dotenv()
TOKEN = os.getenv('TOKEN')
ownerID = os.getenv('owner_id')
intents = discord.Intents.default()


def get_activity():
    with open('activity.json') as f:
        data = json.load(f)
        activity_type = data['activity_type']
        activity_title = data['activity_title']
        activity_url = data['activity_url']
    if activity_type == 'Playing':
        return discord.Game(name=activity_title)
    elif activity_type == 'Streaming':
        return discord.Activity(type=discord.ActivityType.streaming, name=activity_title, url=activity_url)
    elif activity_type == 'Listening':
        return discord.Activity(type=discord.ActivityType.listening, name=activity_title)
    elif activity_type == 'Watching':
        return discord.Activity(type=discord.ActivityType.watching, name=activity_title)
    elif activity_type == 'Competing':
        return discord.Activity(type=discord.ActivityType.competing, name=activity_title)

def get_status():
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

class aclient(discord.AutoShardedClient):
    def __init__(self):
        super().__init__(owner_id = ownerID,
                              intents = intents,
                              status = discord.Status.invisible
                        )
        self.synced = False
    async def on_ready(self):
        logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
        if not self.synced:
            manlogger.info('Syncing...')
            await tree.sync()
            manlogger.info('Synced.')
            self.synced = True
            await self.change_presence(activity = get_activity(), status = get_status())
        global owner
        owner = await bot.fetch_user(ownerID)
        manlogger.info('Initialization completed...')
        manlogger.info('------')
        print('READY')
bot = aclient()
tree = discord.app_commands.CommandTree(bot)

##Events
#Guild Remove
@bot.event
async def on_guild_remove(guild):
    manlogger.info(f'I got kicked from {guild}. (ID: {guild.id})')
#Guild Join
@bot.event
async def on_guild_join(guild):
    manlogger.info(f'I joined {guild}. (ID: {guild.id})')   
#Error
@tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        await interaction.response.send_message(f'This comand is on cooldown.\nTime left: `{seconds_to_minutes(error.retry_after)}`.', ephemeral = True)
        manlogger.warning(str(error)+' '+interaction.user.name+' | '+str(interaction.user.id))
    else:
        await interaction.response.send_message(error, ephemeral = True)
        manlogger.warning(str(error)+' '+interaction.user.name+' | '+str(interaction.user.id))


#Functions
def seconds_to_minutes(input_int):
    return(str(timedelta(seconds=input_int)))

 
##Owner Commands----------------------------------------
#Shutdown
@tree.command(name = 'shutdown', description = 'Savely shut down the bot.')
async def self(interaction: discord.Interaction):
    if interaction.user.id == int(ownerID):
        manlogger.info('Engine powering down...')
        await interaction.response.send_message('Engine powering down...', ephemeral = True)
        await bot.close()
    else:
        await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)
#Get Logs
@tree.command(name = 'get_logs', description = 'Get the current, or all logfiles.')
async def self(interaction: discord.Interaction):
    class LastXLines(discord.ui.Modal, title = 'Line Input'):
        self.timeout = 15
        answer = discord.ui.TextInput(label = 'How many lines?', style = discord.TextStyle.short, required = True, min_length = 1, max_length = 4)
        async def on_submit(self, interaction: discord.Interaction):
            try:
                int(self.answer.value)
            except:
                await interaction.response.send_message(content = 'You can only use numbers!', ephemeral = True)
                return
            if int(self.answer.value) == 0:
                await interaction.response.send_message(content = 'You can not use 0 as a number!', ephemeral = True)
                return
            with open(log_folder+'BotLog.log', 'r', encoding='utf8') as f:
                with open(buffer_folder+'log-lines.txt', 'w', encoding='utf8') as f2:
                    count = 0
                    for line in (f.readlines()[-int(self.answer.value):]):
                        f2.write(line)
                        count += 1
            await interaction.response.send_message(content = f'Here are the last {count} lines of the current logfile:', file = discord.File(r''+buffer_folder+'log-lines.txt') , ephemeral = True)
            if os.path.exists(buffer_folder+'log-lines.txt'):
                os.remove(buffer_folder+'log-lines.txt')
             
    class LogButton(discord.ui.View):
        def __init__(self):
            super().__init__()
            
        @discord.ui.button(label = 'Last X lines', style = discord.ButtonStyle.blurple)
        async def xlines(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            await interaction.response.send_modal(LastXLines())
     
        @discord.ui.button(label = 'Current Log', style = discord.ButtonStyle.grey)
        async def current(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            await interaction.response.defer()
            try:
                await interaction.followup.send(file=discord.File(r''+log_folder+'BotLog.log'), ephemeral=True)
            except discord.HTTPException as err:
                if err.status == 413:
                    with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                        f.write(log_folder+'BotLog.log')
                    try:
                        await interaction.response.send_message(file=discord.File(r''+buffer_folder+'Logs.zip'))
                    except discord.HTTPException as err:
                        if err.status == 413:
                            await interaction.followup.send("The log is too big to be send directly.\nYou have to look at the log in your server(VPS).")
                os.remove(buffer_folder+'Logs.zip')
                            
        @discord.ui.button(label = 'Whole Folder', style = discord.ButtonStyle.grey)
        async def whole(self, interaction: discord.Interaction, button: discord.ui.Button):
            LogButton.stop(self)
            await interaction.response.defer()
            if os.path.exists(buffer_folder+'Logs.zip'):
                os.remove(buffer_folder+'Logs.zip')
            with ZipFile(buffer_folder+'Logs.zip', mode='w', compression=ZIP_DEFLATED, compresslevel=9, allowZip64=True) as f:
                for file in os.listdir(log_folder):
                    if file.endswith(".zip"):
                        continue
                    f.write(log_folder+file)
            try:
                await interaction.followup.send(file=discord.File(r''+buffer_folder+'Logs.zip'), ephemeral=True)
            except discord.HTTPException as err:
                if err.status == 413:
                    await interaction.followup.send("The folder is too big to be send directly.\nPlease get the current file, or the last X lines.")
            
            os.remove(buffer_folder+'Logs.zip')
    if interaction.user.id != int(ownerID):
        await interaction.response.send_message('Only the BotOwner can use this command!', ephemeral = True)
        return
    else:
        await interaction.response.send_message('Send only the current Log, or the whole folder?', view = LogButton(), ephemeral = True)
#Change Activity
@tree.command(name = 'activity', description = 'Change my activity.')
@discord.app_commands.describe(type='The type of Activity you want to set.', title='What you want the bot to play, stream, etc...', url='Url of the stream. Only used if activity set to \'streaming\'.')
@discord.app_commands.choices(type=[
    discord.app_commands.Choice(name='Playing', value='Playing'),
    discord.app_commands.Choice(name='Streaming', value='Streaming'),
    discord.app_commands.Choice(name='Listening', value='Listening'),
    discord.app_commands.Choice(name='Watching', value='Watching'),
    discord.app_commands.Choice(name='Competing', value='Competing')
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
        await bot.change_presence(activity = get_activity(), status = get_status())
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
        await bot.change_presence(activity = get_activity(), status = get_status())
        await interaction.followup.send('Status changed!', ephemeral = True)
    else:
        await interaction.followup.send('Only the BotOwner can use this command!', ephemeral = True)
##Bot Commands----------------------------------------
#Ping
@tree.command(name = 'ping', description = 'Test, if the bot is responding.')
async def self(interaction: discord.Interaction):
    before = time.monotonic()
    await interaction.response.send_message('Pong!')
    ping = (time.monotonic() - before) * 1000
    await interaction.edit_original_response(content=f'Pong! `{int(ping)}ms`')
#Change Nickname
@tree.command(name = 'change_nickname', description = 'Change the nickname of the bot.')
@discord.app_commands.checks.cooldown(1, 60, key=lambda i: (i.guild_id))
@discord.app_commands.checks.has_permissions(manage_nicknames = True)
@discord.app_commands.describe(nick='New nickname for me.')
async def self(interaction: discord.Interaction, nick: str):
    await interaction.guild.me.edit(nick=nick)
    await interaction.response.send_message(f'My new nickname is now **{nick}**.', ephemeral=True)






        
bot.run(TOKEN, log_handler=None)
