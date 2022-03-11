from ast import Return
import os, time, re, csv, a2s, discord, asyncio, config, emoji, sys, colorama, typing, signal, errno
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from colorama import Fore, Style, init
from config import LOGCHAN_ID as lchanID
from config import VCHANNEL_ID as chanID
from config import file
from discord.ext import commands
from socket import timeout
import matplotlib.dates as md
import matplotlib.ticker as ticker
import matplotlib.spines as ms
import pandas as pd
import random
import aiosqlite
import subprocess

#Color init
colorama.init()

pdeath = '.*?Got character ZDOID from ([\w ]+) : (-?\d+:-?\d+)'
pevent = '.*? Random event set:(\w+)'
server_name = config.SERVER_NAME
bot = commands.Bot(command_prefix=';', help_command=None)

def signal_handler(signal, frame):          # Method for catching SIGINT, cleaner output for restarting bot
  os._exit(0)

signal.signal(signal.SIGINT, signal_handler)

async def timenow():
    now = datetime.now()
    gettime = now.strftime("%Y-%m-%d %H:%M:%S")
    return gettime

async def playerdeath(pname):
    lchannel = bot.get_channel(lchanID)
    a = ':skull: **' + pname + '** just died a shameful and humiliating death! Everyone laugh!'
    b = ':skull: **' + pname + '** just died, my bet is a tree gottem!'
    c = ':skull: **' + pname + '** just died, Odin is tired of your crap!'
    d = ':skull: **' + pname + '** just died, how sad.'
    e = ':skull: **' + pname + '** just died from having too much fun!'
    f = ':skull: **' + pname + "** just died, there's got to be a better way " + pname + "!"
    g = ':skull: **' + pname + '** just died from dissing terry!'
    h = ':skull: **' + pname + '** just died and tmoney stole the iron!'
    i = ':skull: **' + pname + '** just died, do you need some help?'
    j = ':skull: **' + pname + '** just died, how many deaths is that now?'
    k = ':skull: **' + pname + '** just died, too much mead?'
    l = ':skull: **' + pname + '** just died, what the hell is happening over there?'
    m = ':skull: **' + pname + '** just died, do you even viking bro?'
    n = ':skull: **' + pname + "** just died, let's try that again shall we?"
    #await asyncio.sleep(1)
    death = random.choice([a,b,c,d,e,f,g,h,i,j])
    await lchannel.send(death)

async def WhatEvent(eventID):
    return {
    'army_eikthyr' : 'EIKTHYR RALLIES THE CREATURES OF THE FOREST - 90 Seconds of Boars and Necks!',
    'army_theelder' : 'THE FOREST IS MOVING... - 120 Seconds of Various Dwarfs!',
    'army_bonemass' : 'A FOUL SMELL FROM THE SWAMP - 150 Seconds of Draugr and Skeletons!',
    'army_moder' : 'A COLD WIND BLOWS FROM THE MOUNTAINS - 150 Seconds of Drakes and Cold!',
    'army_goblin' : 'THE HORDE IS ATTACKING - 120 Seconds of Fulings!',
    'foresttrolls' : 'THE GROUND IS SHAKING - 80 Seconds of Trolls!',
    'blobs' : 'A FOUL SMELL FROM THE SWAMP - 120 Seconds of Blobs and Oozers!',
    'skeletons' : 'SKELETON SURPRISE - 120 Seconds of Skeletons!',
    'surtlings' : 'THERE\'S A SMELL OF SULFUR IN THE AIR - 120 Seconds of Surtlings!',
    'wolves' : 'SOMEONE IS BEING HUNTED - 120 Seconds of Wolves!',
    }[eventID]

async def checkconnect(pname):
    db = await aiosqlite.connect(config.DATABASE)
    lchannel = bot.get_channel(lchanID)
    ccquery = "select isconnected from viking where name = '%s'" %(pname)
    cccursor = await db.cursor()
    await cccursor.execute(ccquery)
    ccc = await cccursor.fetchone()
    await cccursor.close()
    print('checkconnect() ccc ',ccc)
    if ccc is None or ccc[0] == 0:
        await lchannel.send(pname +'** just connected! **')

# Basic file checking
# def check_csvs():
#     try: 
#         os.makedirs('csv')
#     except OSError as e:
#         if e.errno != errno.EEXIST:
#             print(Fore.RED + 'Cannot create csv directory' + Style.RESET_ALL)
#             raise os._exit(1)

#     files = ['csv/playerstats.csv']
#     for f in files:
#         if os.path.isfile(f):
#             print(Fore.GREEN + f'{f} found!' + Style.RESET_ALL)
#         else:
#             with open(f, 'w+'):
#                 print(Fore.YELLOW + f'{f} doesn\'t exist, creating new...' + Style.RESET_ALL)
#             time.sleep(0.2)

# check_csvs()

@bot.event
async def on_ready():
    print(Fore.GREEN + f'Bot connected as {bot.user} :)' + Style.RESET_ALL)
    print('Log channel : %d' % (lchanID))
    if config.USEVCSTATS == True:
        print('VoIP channel: %d' % (chanID))
        bot.loop.create_task(serverstatsupdate())

@bot.command(name='helpadmin')
@commands.has_role('Admin')
async def help_ctx(ctx):  
    help_embed = discord.Embed(description="**Bayou's Valheim Discord Bot - ADMIN COMMANDS**", color=0x33a163,)
    # whitelist
    help_embed.add_field(name="{}whitelist STEAMID".format(bot.command_prefix), 
                        value="Whitelist player's steamid for server access. \n Example:`{}whitelist 12345678901234567` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    # ban
    help_embed.add_field(name="{}ban STEAMID".format(bot.command_prefix), 
                        value="Ban player's steamid for server access. Does not remove player from DB. \n Example:`{}ban 12345678901234567` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    # evict
    help_embed.add_field(name="{}evict STEAMID".format(bot.command_prefix), 
                        value="Evict player's steamid for server access and remove them from the DB. \n Example:`{}evict 12345678901234567` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    # playersid
    help_embed.add_field(name="{}playersid".format(bot.command_prefix), 
                        value="List player's steamid. \n Example:`{}playersid` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    # serverrestart
    help_embed.add_field(name="{}serverrestart".format(bot.command_prefix), 
                        value="Restarts the Server. \n Example:`{}serverrestart` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    #serverupdate
    help_embed.add_field(name="{}serverupdate".format(bot.command_prefix), 
                        value="Updates the Server. \n Example:`{}serverupdate` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    # purgestats
    help_embed.add_field(name="{}purgestats".format(bot.command_prefix), 
                        value="Deletes stats db (for when the ;stats command is slow). \n Example:`{}purgestats` \n Only available when Admin role is assigned".format(bot.command_prefix),
                        inline=True)
    help_embed.set_footer(text="BValbot v0.5")
    await ctx.send(embed=help_embed)

@bot.command(name='help')
async def help_ctx(ctx):  
    help_embed = discord.Embed(description="**Bayou's Valheim Discord Bot**", color=0x33a163,)
    # stats
    help_embed.add_field(name="{}stats <n>".format(bot.command_prefix),
                        value="Plots a graph of connected players over the last X hours.\n Example: `{}stats 12` \n Available: 24, 12, w (*default: 24*)".format(bot.command_prefix),
                        inline=True)
    # deaths
    help_embed.add_field(name="{}deaths".format(bot.command_prefix), 
                        value="Shows a top 10 leaderboard of players with the most deaths. \n Example:`{}deaths`".format(bot.command_prefix),
                        inline=True)
    # players
    help_embed.add_field(name="{}players".format(bot.command_prefix), 
                        value="Shows players logged on. \n Example:`{}players`".format(bot.command_prefix),
                        inline=True)
    # time
    help_embed.add_field(name="{}time".format(bot.command_prefix), 
                        value="Shows total play time of each player. \n Example:`{}time`".format(bot.command_prefix),
                        inline=True)
    # last
    help_embed.add_field(name="{}last".format(bot.command_prefix), 
                        value="Shows players last logon time. \n Example:`{}last`".format(bot.command_prefix),
                        inline=True)
    # eviction
    help_embed.add_field(name="{}eviction".format(bot.command_prefix), 
                        value="Shows players eligible for eviction! \n Example:`{}eviction`".format(bot.command_prefix),
                        inline=True)
    # flip
    help_embed.add_field(name="{}flip".format(bot.command_prefix), 
                        value="Performs a coin flip returning Heads or Tails. \n Example:`{}flip`".format(bot.command_prefix),
                        inline=True)
    # yes no
    help_embed.add_field(name="{}yesno".format(bot.command_prefix), 
                        value="Decides yes or no. \n Example:`{}yesno`".format(bot.command_prefix),
                        inline=True)
    #magic 8 ball
    help_embed.add_field(name="{}magic8ball".format(bot.command_prefix), 
                        value="Ask the Magic 8 Ball! \n Example:`{}magic8ball`".format(bot.command_prefix),
                        inline=True)
    help_embed.set_footer(text="BValbot v0.5")
    await ctx.send(embed=help_embed)

@bot.command(name="deaths")
async def leaderboards(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    top_no = 10
    ldrembed = discord.Embed(title=":skull_crossbones: __Death Leaderboards (top 10)__ :skull_crossbones:", color=0xFFC02C)
    dquery = "select deathtime, charname from deaths"
    dcursor = await db.cursor()
    await dcursor.execute(dquery)
    dcfetch = await dcursor.fetchall()
    await dcursor.close()
    df = pd.DataFrame(dcfetch, columns =['deathtime', 'charname'])
    df_index = df['charname'].value_counts().nlargest(top_no).index
    df_score = df['charname'].value_counts().nlargest(top_no)
    x = 0
    l = 1 #just in case I want to make listed iterations l8r
    for ind in df_index:
        grammarnazi = 'deaths'
        leader = ''
        # print(df_index[x], df_score[x]) 
        if df_score[x] == 1 :
            grammarnazi = 'death'
        if l == 1:
            leader = ':crown:'
        ldrembed.add_field(name="{} {}".format(df_index[x],leader),
                           value='{} {}'.format(df_score[x],grammarnazi),
                           inline=False)
        x += 1
        l += 1
    await ctx.send(embed=ldrembed)

@bot.command(name="time")
async def timeboards(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    ldrembed = discord.Embed(title="::hourglass:: __Time Online__ ::hourglass::", color=0x1f8b4c)
    tquery = "select name, dctime from viking order by dctime desc"
    tcursor = await db.cursor()
    await tcursor.execute(tquery)
    tfetch = await tcursor.fetchall()
    await tcursor.close()
    df = pd.DataFrame(tfetch, columns =['name', 'dctime'])
    numrows = df.shape[0]
    i = 0
    while i < numrows:
        tmin = df.loc[i,'dctime']
        tname = df.loc[i,'name']
        tswap = ''
        if tmin < 60:
            tswap = "minutes"
        elif tmin < 1440:
            tmin = round(tmin / 60, 1)
            tswap = "hours"
        else:
            tmin = round((tmin / 60) / 24, 2)
            tswap = "days"
        ldrembed.add_field(name="{}".format(tname),value="{} {}".format(tmin,tswap),inline=False)
        i = i + 1
    await ctx.send(embed=ldrembed)

@bot.command(name="eviction")
async def evictioncheck(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    equery = "select name, jointime from viking order by jointime desc"
    ecursor = await db.cursor()
    await ecursor.execute(equery)
    efetch = await ecursor.fetchall()
    await ecursor.close()
    dt = pd.DataFrame(efetch, columns =['name', 'jointime'])
    ldrembed = discord.Embed(title=":mans_shoe: __Eviction Notice (5 Days Absent)__ :house_with_garden:", color=0x1f8b4c)
    dt['jointime'] = pd.to_datetime(dt['jointime'], format="%Y-%m-%d %H:%M:%S")
    numrows = dt.shape[0]
    i = 0
    while i < numrows:
        lastlogon = dt.loc[i,"jointime"]
        eplayer = dt.loc[i,'name']
        evictiontime = 5
        time = await timenow()
        tdelta = datetime.strptime(time,"%Y-%m-%d %H:%M:%S") - lastlogon
        #tdelta = datetime.strptime(time,"%Y-%m-%d %H:%M:%S") - datetime.strptime(lastlogon,"%Y-%m-%d %H:%M:%S")
        totaltime = round((tdelta.total_seconds()/60),2)
        timeinhours = totaltime / 60
        timeindays = round((timeinhours / 24),2)
        elastlogon = lastlogon.strftime("%m-%d %I:%M%p")
        if timeindays > evictiontime:
            #print(eplayer,elastlogon,timeindays,'days',eviction)
            ldrembed.add_field(name="{}".format(eplayer),value="{} Days __EVICTION NOTICE!!!__".format(elastlogon),inline=False)
        i = i + 1
    await ctx.send(embed=ldrembed)

@bot.command(name="last")
async def lastloglist(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    ldrembed = discord.Embed(title=":clock9: __Last Logon__ :clock9:", color=0x1f8b4c)
    lquery = "select name, jointime from viking order by jointime desc"
    lcursor = await db.cursor()
    await lcursor.execute(lquery)
    lfetch = await lcursor.fetchall()
    await lcursor.close()
    dt = pd.DataFrame(lfetch, columns =['name', 'jointime'])
    dt['jointime'] = pd.to_datetime(dt['jointime'], format="%Y-%m-%d %H:%M:%S")
    numrows = dt.shape[0]
    i = 0
    while i < numrows:
        lastlogon = dt.loc[i,"jointime"]
        eplayer = dt.loc[i,'name']
        elastlogon = lastlogon.strftime("%m-%d %I:%M%p")
        #print(eplayer,elastlogon,timeindays)
        ldrembed.add_field(name="{}".format(eplayer),value="Last Logon: {}".format(elastlogon),inline=False)
        i = i + 1
    await ctx.send(embed=ldrembed)

@bot.command(name="players")
async def playerson(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    pquery = "select name, jointime from viking where isconnected = 1"
    pcursor = await db.cursor()
    await pcursor.execute(pquery)
    pfetch = await pcursor.fetchall()
    await pcursor.close()
    dt = pd.DataFrame(pfetch, columns =['name', 'jointime'])
    print(dt)
    if dt.empty:
        await ctx.send('No Players Online')
    else:
        ldrembed = discord.Embed(title=":man: __Players Online__ :woman:", color=0x1f8b4c)
        dt['jointime'] = pd.to_datetime(dt['jointime'], format="%Y-%m-%d %H:%M:%S")
        numrows = dt.shape[0]
        i = 0
        while i < numrows:
            lastlogon = dt.loc[i,"jointime"]
            eplayer = dt.loc[i,'name']
            elastlogon = lastlogon.strftime("%m-%d %I:%M%p")
            ldrembed.add_field(name="{}".format(eplayer),value="Logged on since: {}".format(elastlogon),inline=False)
            i = i + 1
        await ctx.send(embed=ldrembed)

@bot.command(name="playersid")
@commands.has_role('Admin')
async def playerson(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    ldrembed = discord.Embed(title=":man: __Player's SteamID__ :woman:", color=0x1f8b4c)
    pquery = "select name, steamid from viking"
    pcursor = await db.cursor()
    await pcursor.execute(pquery)
    pfetch = await pcursor.fetchall()
    await pcursor.close()
    dt = pd.DataFrame(pfetch, columns =['name', 'steamid'])
    numrows = dt.shape[0]
    i = 0
    while i < numrows:
        pid = dt.loc[i,"steamid"]
        eplayer = dt.loc[i,'name']
        ldrembed.add_field(name="{}".format(eplayer),value="SteamID: {}".format(pid),inline=False)
        i = i + 1
    await ctx.send(embed=ldrembed)

@bot.command(name="whitelist",pass_context=True)
@commands.has_role('Admin')
async def whitelist(ctx,whsteamid):
    if len(whsteamid) == 17:
        cmd = 'echo ' + whsteamid + " >> /home/vhserver2/.config/unity3d/IronGate/Valheim/permittedlist.txt"
        os.system(cmd)
        ldrembed = discord.Embed(title="Player Whitelisted", color=0x1f8b4c)
        await ctx.send(embed=ldrembed)

#////////////////////////////////////////////////////////////////////////////////////////////////////////////
# I bypassed the error by commenting out the following lines in ~/lgsm/functions/check_tmuxception.sh:
# fn_check_is_in_tmux
# fn_check_is_in_screen

@bot.command(name="serverrestart")
@commands.has_role('Admin')
async def restartserver(ctx):
    cmd = "/home/vhserver2/vhserver"
    arg = "r"
    subprocess.run([cmd,arg]) # ,stdout=subprocess.DEVNULL
    #os.system(cmd)
    #list_files = subprocess.run(["ls", "-l"], stdout=subprocess.DEVNULL)
    await ctx.send(':loudspeaker: ** Server Restart **')

@bot.command(name="serverupdate")
@commands.has_role('Admin')
async def restartserver(ctx):
    cmd = "/home/vhserver2/vhserver"
    arg = "u"
    subprocess.run([cmd,arg],stdout=subprocess.DEVNULL)
    await ctx.send(':loudspeaker: ** Server Updating **')

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////

@bot.command(name="flip")
async def flipcoin(ctx):
    flip = random.choice(['Heads', 'Tails'])
    await ctx.send(flip)

@bot.command(name="yesno")
async def yesno(ctx):
    yesno = random.choice(['Yes', 'No'])
    await ctx.send(yesno)

@bot.command(name="magic8ball")
async def yesno(ctx):
    answers = ['It is certain',
                'It is decidedly so',
                'Without a doubt',
                'Yes – definitely',
                'You may rely on it',
                'As I see it, yes',
                'Most likely',
                'Outlook good',
                'Yes Signs point to yes',
                'Reply hazy',
                'try again',
                'Ask again later',
                'Better not tell you now',
                'Cannot predict now',
                'Concentrate and ask again',
                'Dont count on it',
                'My reply is no',
                'My sources say no',
                'Outlook not so good',
                'Very doubtful']
    magicball = answers[random.randint(0, len(answers)-1)]
    await ctx.send(magicball)

def check_csvs():
    try: 
        os.makedirs('csv')
    except OSError as e:
        if e.errno != errno.EEXIST:
            print(Fore.RED + 'Cannot create csv directory' + Style.RESET_ALL)
            raise os._exit(1)

    files = ['csv/playerstats.csv']
    for f in files:
        if os.path.isfile(f):
            print(Fore.GREEN + f'{f} found!' + Style.RESET_ALL)
        else:
            with open(f, 'w+'):
                print(Fore.YELLOW + f'{f} doesn\'t exist, creating new...' + Style.RESET_ALL)
            time.sleep(0.2)

check_csvs()

@bot.command(name="tmoneystoletheiron")
async def tmoney(ctx):
    await ctx.send('TMONEY STOLE MY DAMN IRON AGAIN!!!')

@bot.command(name="whoistmoney")
async def tmoney(ctx):
    await ctx.send('TMONEY IS A DIRTY IRON THIEF!!!')

@bot.command(name="ban",pass_context=True)
@commands.has_role('Admin')
async def banplayer(ctx,whsteamid):
    if len(whsteamid) == 17:
        line = "'/"+whsteamid+"/d'"
        cmd = 'sed -i ' + line + " /home/vhserver2/.config/unity3d/IronGate/Valheim/permittedlist.txt"
        os.system(cmd)
        ldrembed = discord.Embed(title="Player Banned", color=0x1f8b4c)
        await ctx.send(embed=ldrembed)

@bot.command(name="evict",pass_context=True)
@commands.has_role('Admin')
async def evict(ctx,esteamid):
    db = await aiosqlite.connect(config.DATABASE)
    if len(esteamid) == 17:
        line = "'/"+esteamid+"/d'"
        cmd = 'sed -i ' + line + " /home/vhserver2/.config/unity3d/IronGate/Valheim/permittedlist.txt"
        os.system(cmd)
        playerquery = "delete from characters where steamid = %s" %(esteamid)
        isccursor = await db.cursor()
        await isccursor.execute(playerquery)
        playerquery = "delete from connect where steamid = %s" %(esteamid)
        await isccursor.execute(playerquery)
        playerquery = "delete from deaths where steamid = %s" %(esteamid)
        await isccursor.execute(playerquery)
        playerquery = "delete from viking where steamid = %s" %(esteamid)
        await isccursor.execute(playerquery)
        await db.commit()
        await isccursor.close()
        ldrembed = discord.Embed(title="Player Evicted", color=0x1f8b4c)
        await ctx.send(embed=ldrembed)
    else:
        await ctx('**Check SteamID Length!**')

@bot.command(name="bayoupurge")
@commands.has_role('Admin')
async def bayoupurgedb(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    playerquery = "delete from characters"
    isccursor = await db.cursor()
    await isccursor.execute(playerquery)
    playerquery = "delete from connect"
    await isccursor.execute(playerquery)
    playerquery = "delete from deaths"
    await isccursor.execute(playerquery)
    playerquery = "delete from playerc"
    await isccursor.execute(playerquery)
    playerquery = "delete from viking"
    await isccursor.execute(playerquery)
    await db.commit()
    await isccursor.close()
    ldrembed = discord.Embed(title="DB Purged", color=0x1f8b4c)
    await ctx.send(embed=ldrembed)

@bot.command(name="purgestats")
@commands.has_role('Admin')
async def bayoupurgedb(ctx):
    db = await aiosqlite.connect(config.DATABASE)
    isccursor = await db.cursor()
    playerquery2 = "delete from playerc"
    await isccursor.execute(playerquery2)
    await db.commit()
    await isccursor.close()
    ldrembed = discord.Embed(title="Stats Purged", color=0x1f8b4c)
    await ctx.send(embed=ldrembed)

@bot.command(name="stats")
async def gen_plot(ctx, tmf: typing.Optional[str] = '24'):
    user_range = 0
    if tmf.lower() in ['w', 'week', 'weeks']:
        user_range = 168 - 1
        interval = 24
        date_format = '%m/%d'
        timedo = 'week'
        description = 'Players online in the past ' + timedo + ':'
    elif tmf.lower() in ['12', '12hrs', '12h', '12hr']:
        user_range = 12 - 0.15
        interval = 1
        date_format = '%H'
        timedo = '12hrs'
        description = 'Players online in the past ' + timedo + ':'
    else:
        user_range = 24 - 0.30
        interval = 2
        date_format = '%H'
        timedo = '24hrs'
        description = 'Players online in the past ' + timedo + ':'

    # db = await aiosqlite.connect(config.DATABASE)
    # pquery = "select time, pcount from playerc order by time desc"
    # pcursor = await db.cursor()
    # await pcursor.execute(pquery)
    # pfetch = await pcursor.fetchall()
    # await pcursor.close()
    # df = pd.DataFrame(pfetch)
    # df[0] = pd.to_datetime(df[0], format="%d-%m-%Y %H:%M:%S")
    #Get data from csv
    df = pd.read_csv('csv/playerstats.csv', header=None, usecols=[0, 1], parse_dates=[0], dayfirst=True)
    lastday = datetime.now() - timedelta(hours = user_range)
    last24 = df[df[0]>=(lastday)]

    # Plot formatting / styling matplotlib
    plt.style.use('seaborn-pastel')
    plt.minorticks_off()
    fig, ax = plt.subplots()
    ax.grid(b=True, alpha=0.2)
    ax.set_xlim(lastday, datetime.now())
    # ax.set_ylim(0, 10) Not sure about this one yet
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.xaxis.set_major_formatter(md.DateFormatter(date_format))
    ax.xaxis.set_major_locator(md.HourLocator(interval=interval))
    for spine in ax.spines.values():
        spine.set_visible(False)
    for tick in ax.get_xticklabels():
        tick.set_color('gray')
    for tick in ax.get_yticklabels():
        tick.set_color('gray')
    
    #Plot and rasterize figure
    plt.gcf().set_size_inches([5.5,3.0])
    plt.plot(last24[0], last24[1])
    plt.tick_params(axis='both', which='both', bottom=False, left=False)
    plt.margins(x=0,y=0,tight=True)
    plt.tight_layout()
    fig.savefig('temp.png', transparent=True, pad_inches=0) # Save and upload Plot
    image = discord.File('temp.png', filename='temp.png')
    plt.close()
    embed = discord.Embed(title=server_name, description=description, colour=12320855)
    embed.set_image(url='attachment://temp.png')
    await ctx.send(file=image, embed=embed)

async def mainloop(file):
    await bot.wait_until_ready()
    lchannel = bot.get_channel(lchanID)
    print('Main loop: init')
    try:
        testfile = open(file)
        testfile.close()
        while not bot.is_closed():
            with open(file, encoding='utf-8', mode='r') as f:
                f.seek(0,2)
                while True:
                    line = f.readline()
                    if(re.search(pdeath, line)):
                        pname = re.search(pdeath, line).group(1)
                        pnumb = re.search(pdeath, line).group(2)
                        if pnumb == '0:0':
                            await playerdeath(pname)
                        # else:
                        #     await checkconnect(pname)
                    if(re.search(pevent, line)):
                        eventID = re.search(pevent, line).group(1)
                        nevent = await WhatEvent(eventID)
                        # debug info
                        print(nevent)
                        await lchannel.send(':loudspeaker: **' + nevent + '**')
                    await asyncio.sleep(0.2)
    except IOError:
        print('No valid log found, event reports disabled. Please check config.py')
        print('To generate server logs, run server with -logfile launch flag')  

async def serverstatsupdate():
	await bot.wait_until_ready()
	while not bot.is_closed():
		try:
			server = a2s.info(config.SERVER_ADDRESS)
			channel = bot.get_channel(chanID)
			await channel.edit(name=f"{emoji.emojize(':person_raising_hand:')} In-Game: {server.player_count}" +" / 10") ## put max server count here
		except timeout:
			print(Fore.RED + await timenow(), 'No reply from A2S, retrying (30s)...' + Style.RESET_ALL)
			channel = bot.get_channel(chanID)
			await channel.edit(name=f"{emoji.emojize(':cross_mark:')} Server Offline")
		await asyncio.sleep(30)
        
bot.loop.create_task(mainloop(file))
bot.run(config.BOT_TOKEN)(file))
bot.run(config.BOT_TOKEN)
