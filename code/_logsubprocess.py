from datetime import datetime
from socket import timeout
import time, os, re, a2s
from unicodedata import name
import csv, asyncio
import config
import pandas as pd
import aiosqlite

## CREATE TABLE viking (steamid text, name text, deaths int default 0, jointime text, dctime int default 0, isconnected int default 0)
## CREATE TABLE characters (steamid text, playerchar text)
## CREATE TABLE connect (steamid text, jointime text, badpw default 0)
## CREATE TABLE deaths (steamid text, charname text, deathtime text)
## CREATE TABLE playerc (time text, pcount int)
## original work - 
## project started as an attempt to adapt csv storage to MySQL 
## Added new regex define to pickup spaces, if character names have additional characters and are not being picked up add them inside brackets i.e. [\w ']+
## regex101.com will assist with making sure names are parsed correctly
## use pdeath inside quotes as search criteria
## use '10/12/2021 01:14:24: Got character ZDOID from Example : 0:0' as search string

pdeath = '.*?Got character ZDOID from ([\w ]+) : (-?\d+:-?\d+)'
steamid = 'Got handshake from client ([\d]+)'
wrongpw = 'Peer ([\d]+) has wrong password'
disconnect = 'Closing socket (\d{2,})'
log = config.file

async def getplayersteamid(gpname):
    db = await aiosqlite.connect(config.DATABASE)
    steamidquery = "select steamid from viking where name = ('%s')" %(gpname)
    #debug info
    print('getplayersteamid()',steamidquery)
    gpidcursor = await db.cursor()
    await gpidcursor.execute(steamidquery)
    gpid = await gpidcursor.fetchone()
    await gpidcursor.close()
    #debug info
    print('getplayersteamid-Got Name (%s)' %(gpname))
    return gpid

async def getplayername(gpsteamid):
    db = await aiosqlite.connect(config.DATABASE)
    namequery = "select name from viking where steamid = (%s)" %(gpsteamid)
    gpcursor = await db.cursor()
    await gpcursor.execute(namequery)
    gpname = await gpcursor.fetchone()
    await gpcursor.close()
    # debug info
    # print('getplayername-Got Steam ID (%s)' %(gpsteamid))
    return gpname

async def playerconnected(pcsteamid, pcname, pcjointime):
    db = await aiosqlite.connect(config.DATABASE)
    playerquery = "select name from viking where steamid = '%s'" %(pcsteamid)
    #debug info
    print('playerconnected()',playerquery)
    pccursor = await db.cursor()
    await pccursor.execute(playerquery)
    pcid = await pccursor.fetchone()
    # if a name exist
    if pcid:
        # # debug info
        # print(pcname,pcid[0])
        # # does the name match existing name?
        # if pcname == pcid[0]:
        #     # if not connected (table viking column is connected = 0)
        if await isconnected(pcsteamid) == 0:
            pctquery = "update viking set name = '%s', jointime = '%s', isconnected = 1 where steamid = '%s'" %(pcname,pcjointime,pcsteamid)
            print('playerconnected()',pctquery)
            await pccursor.execute(pctquery)
            await db.commit()
            await pccursor.close()
            #name exist in the viking table, viking exist already and is updated
            # else:
                # (table viking column is connected = 1)
                # death event has occured since connected should = 1
        # else:
        #     # fix for death overwrite of name/id
        #     if await isconnected(pcsteamid) == 0:
        #         # player has a new name, but steam id exist
        #         pctquery = "update viking set name = '%s', jointime = '%s', isconnected = 1 where steamid = '%s'" %(pcname,pcjointime,pcsteamid)
        #         await pccursor.execute(pctquery)
        #         # debug info
        #         print('playerconnect() new name set in viking - ',pctquery)
        #         pctequery = "insert into characters (steamid, playerchar) values ('%s','%s')" %(pcsteamid,pcname)
        #         # debug info
        #         print('playerconnected() new character added',pctequery)
        #         await pccursor.execute(pctequery)
        #         await asyncio.sleep(1)
        #         await db.commit()
        #         await pccursor.close()
        #         # print("Viking updated")
    else:
        # new viking added 
        elquery = "insert into viking (steamid, name, jointime,isconnected) values ('%s', '%s', '%s', %s)" %(pcsteamid,pcname,pcjointime,1)
        # debug info
        print('playerconnected() new viking added - ',elquery)
        await pccursor.execute(elquery)
        await db.commit()
        await pccursor.close()
        # debug info 
        # print ("New viking added")
        return

async def updatebadpw(pcsteamid,pwstate):
    db = await aiosqlite.connect(config.DATABASE)
    pctcursor = await db.cursor()
    pctquery = "update connect set badpw = %s where steamid = '%s'" %(pwstate,pcsteamid)
    # debug info
    print('updatebpw()', pctquery)
    await pctcursor.execute(pctquery)
    await db.commit()
    await pctcursor.close()

async def getbadpw(pcsteamid):
    db = await aiosqlite.connect(config.DATABASE)
    bpwquery = "select badpw from connect where steamid = (%s)" %(pcsteamid)
    bpwcursor = await db.cursor()
    await bpwcursor.execute(bpwquery)
    bpwstat = await bpwcursor.fetchone()
    await bpwcursor.close()
    print('getbadpw()', bpwstat)
    return bpwstat[0]

async def playerconnect(pctsteamid, pctjointime):
    db = await aiosqlite.connect(config.DATABASE)
    pctcursor = await db.cursor()
    #required for MySQL
    #pctkey = "set foreign_key_checks=0;"
    #pctcursor.execute(pctkey)
    pctquery = '''insert into connect (steamid, jointime) values ('%s','%s')''' %(pctsteamid,pctjointime)
    print('playerconnect()', pctquery)
    await pctcursor.execute(pctquery)
    await db.commit()
    await pctcursor.close()
    print('playerconnect - Player connect')

async def playerdc(dcsteamid,dctime):
    db = await aiosqlite.connect(config.DATABASE)
    # in case player connect does not initiate, keeps long time periods from being added (last current time - last logon)
    if await isconnected(dcsteamid) == 0:
        # debug info       
        print("playerdc() - not connected")
        return
    # required check in case new player gets pw wrong!
    elif await getbadpw(dcsteamid) == 0:
        pdccursor = await db.cursor()
        pjtquery = "select jointime from viking where steamid = '%s'" %(dcsteamid)
        await pdccursor.execute(pjtquery)
        pjtime = await pdccursor.fetchone()
        # debug info
        print('playerdc() pjtime = ',pjtime)
        try:
            t1 = pjtime[0]
        except:
            print("t1 does not exist")
            return
        t2 = dctime
        # create datetime from str for calculation
        tdelta = datetime.strptime(t2,"%Y-%m-%d %H:%M:%S") - datetime.strptime(t1,"%Y-%m-%d %H:%M:%S")
        # time in minutes
        totaltime = round(((tdelta.total_seconds())/60),2)
        # debug info
        print("playerdc - total time", totaltime)
        dctquery = "select dctime from viking where steamid = '%s'" %(dcsteamid)
        await pdccursor.execute(dctquery)
        dtime = await pdccursor.fetchone()
        # debug info
        print('playerdc() pjtime = ',dtime)
        # player has no play time 0 or None
        if dtime[0] == None:
            # add time played to viking table
            pctquery = "update viking set dctime = '%s', isconnected = 0 where steamid = '%s'" %(totaltime,dcsteamid)
            print('playerdc()',pctquery)
            await pdccursor.execute(pctquery)
            await db.commit()
            await pdccursor.close()
            # debug info
            # print("playerdc - Player time added")
        else:
            # calculate time played + previous time played
            texist = round(dtime[0],2)
            newtime = round(texist + totaltime,2)
            # debug info
            print("playerdc - dctime ", dtime[0])
            # required for MySQL
            # pctkey = "set foreign_key_checks=0;"
            # pctcursor.execute(pctkey)
            pctquery = "update viking set dctime = '%s', isconnected = 0 where steamid = '%s'" %(newtime,dcsteamid)
            # debug info
            print('playerdc()',pctquery)
            await pdccursor.execute(pctquery)
            await db.commit()
            await pdccursor.close()
            # debug info
            # print("playerdc - newtime",newtime)
            # print("playerdc - Player time updated")

async def playerdeath(pdname,pdtime):
    db = await aiosqlite.connect(config.DATABASE)
    pdcursor = await db.cursor()
    pdsteamid = await getplayersteamid(pdname)
    # debug info
    if pdsteamid:
        print('playerdeath()',pdsteamid)
        pdquery = "update viking set deaths = deaths + 1 where steamid = '%s'" %(pdsteamid[0])
        await pdcursor.execute(pdquery)
        pdquery = "insert into deaths (steamid, charname, deathtime) values ('%s','%s','%s')" %(pdsteamid[0],pdname,pdtime)
        # debug info
        print('playerdeath()',pdquery)
        await pdcursor.execute(pdquery)
        await db.commit()
        await pdcursor.close()

async def isconnected(iscsteamid):
    db = await aiosqlite.connect(config.DATABASE)
    # debug info
    print('is connected checking for id:',iscsteamid)
    playerquery = "select isconnected from viking where steamid = '%s'" %(iscsteamid)
    isccursor = await db.cursor()
    await isccursor.execute(playerquery)
    iscstatus = await isccursor.fetchone()
    # debug info
    print("isconnected 1 = yes 0 = no",iscstatus)
    # debug info
    if iscstatus:
        if iscstatus[0] in (0,None):
            isc = 0
            print ("isconnected - player not connected")
        elif iscstatus[0] == 1:
            isc = 1
            print ("isconnected - player connected")
        else:
            print ("isconnected - Player does not exist yet")
            isc = None
    else:
        isc = None
    await isccursor.close()
    #debug info
    print("isconnected value",isc)
    return isc

# get last steam id for connect
async def getlaststeamid():
    db = await aiosqlite.connect(config.DATABASE)
    lsteamid = "select steamid from connect order by jointime DESC"
    # debug info
    print('getlaststeamid()', lsteamid)
    print(lsteamid[0])
    glcursor = await db.cursor()
    await glcursor.execute(lsteamid)
    glid = await glcursor.fetchone()
    await glcursor.close()
    return glid[0]

async def search(list, platform):
    for i in range(len(list)):
        if list[i] == platform:
            return True
    return False

async def timenow():
    now = datetime.now()
    gettime = now.strftime("%Y-%m-%d %H:%M:%S")
    return gettime

async def ctimenow():
    now = datetime.now()
    gettime = now.strftime("%d-%m-%Y %H:%M:%S")
    return gettime

async def writepcount():
    while True:
        try:
            server = a2s.info(config.SERVER_ADDRESS)
            with open('csv/playerstats.csv', 'a', newline='') as f:
                csvup = csv.writer(f, delimiter=',')
                curtime, players = await ctimenow(), server.player_count
                csvup.writerow([curtime, players])
                print(curtime, players)
        except timeout:
            with open('csv/playerstats.csv', 'a', newline='') as f:
                csvup = csv.writer(f, delimiter=',')
                curtime, players = await ctimenow(), '0'
                csvup.writerow([curtime, players])
                print(curtime, 'Cannot connect to server')
        await asyncio.sleep(60)

# async def writepcount():
#     while True:
#         try:
#             server = a2s.info(config.SERVER_ADDRESS)
#             try:
#                 db = await aiosqlite.connect(config.DATABASE)
#             except:
#                 print('connection error')
#                 return
#             pdcursor = await db.cursor()
#             curtime, players = await ctimenow(), server.player_count
#             pdquery = "insert into playerc (time, pcount) values ('%s',%s)" %(curtime,players)
#             try:
#                 await pdcursor.execute(pdquery)
#                 await db.commit()
#                 await pdcursor.close()
#             except aiosqlite.Error:
#                 print("aiosqlite error")
#                 return
#             print(curtime, players)
#         except timeout:
#             try:
#                 db = await aiosqlite.connect(config.DATABASE)
#                 pdcursor = await db.cursor()
#             except:
#                 print('connection error')
#                 return
#             curtime, players = await ctimenow(), server.player_count
#             pdquery = "insert into playerc (time, pcount) values ('%s',%s)" %(curtime,players)
#             try:
#                 await pdcursor.execute(pdquery)
#                 await db.commit()
#                 await pdcursor.close()
#             except aiosqlite.Error:
#                 print("aiosqlite error")
#                 return
#             print(curtime, 'Cannot connect to server')
#         await asyncio.sleep(60)

async def logscrape():
    while True:
        with open(log, encoding='utf-8', mode='r') as log_file:
            log_file.seek(0,2)
            while True:
                line = log_file.readline()
                if(re.search(steamid, line)):
                    steamnumber = re.search(steamid, line).group(1)
                    curtime = await timenow()
                    await playerconnect(steamnumber,curtime)
                if(re.search(wrongpw, line)):
                    stupidc = re.search(wrongpw, line).group(1)
                    #print('calling wrong password - updatebapw 1')
                    await updatebadpw(stupidc,1)
                if(re.search(pdeath, line)):
                    pname = re.search(pdeath, line).group(1)
                    dnumb = re.search(pdeath, line).group(2)
                    if dnumb == '0:0':
                        curtime = await timenow()
                        await playerdeath(pname,curtime)
                        #print("deathcount 0:0 event",curtime, pname, ' has died!')
                    else:
                        curtime = await timenow()
                        elsteamid = await getlaststeamid()
                        await playerconnected(elsteamid,pname,curtime)
                        await updatebadpw(elsteamid,0)
                if(re.search(disconnect, line)):
                        dcplayer = re.search(disconnect, line).group(1)
                        curtime = await timenow()
                        await playerdc(dcplayer,curtime)
                        #print('calling wrong password - updatebapw 2')
                await asyncio.sleep(0.2)

loop = asyncio.get_event_loop()
loop.create_task(logscrape())
loop.create_task(writepcount())
loop.run_forever()
