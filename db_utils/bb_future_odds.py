import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
sys.path.insert(-1, os.path.join(cur_path, 'model_conf'))
sys.path.insert(-1, cur_path)
import bb_odds
  
def update(cnx):
    import requests
    from lxml import html
    import datetime
    from mysql.connector import IntegrityError, DataError
    from datetime import date
    
    print('Starting NCAA Basketball Odds Update')
   
    cursor = cnx.cursor() 
    cursor.execute('SET SQL_SAFE_UPDATES = 0;')
    cursor.execute('DELETE FROM ncaa_bb.future_games;')
    cursor.execute('SET SQL_SAFE_UPDATES = 1;')
    cnx.commit()
    offseason = [5,6,7,8,9,10]
    cursor.execute('select max(oddsdata.oddsdate) from ncaa_bb.oddsdata')
    x = cursor.fetchall()
    start_date = x[0][0]
    date1 = datetime.datetime.now()
    date1 = date1 + datetime.timedelta(days=+7)
    dates = []
    stop_date = datetime.datetime.now() + datetime.timedelta(days=+7)
    while start_date <= date(stop_date.year,stop_date.month,stop_date.day):
        urldate = '%s-%s-%s' % (start_date.year, start_date.month, start_date.day)
        if start_date.month not in offseason:
            dates.append(urldate)
        start_date = start_date + datetime.timedelta(days=1)
        
    teamnames = bb_odds.teamnames
    teamlist = bb_odds.teamlist
    nond1 = bb_odds.nond1
    
    oddsteamsdict = {}
    for i in range(0, len(teamnames)):
        oddsteamsdict[teamlist[i].upper()] = teamnames[i]        
    nonfbsteams = []
    all_games = []
    all_errors = []
    favorite_errors = []
    spot = 0
    if len(dates) > 0:
        for gameday in dates:
                spot += 1
                print('%.2f percent complete' % ((float(spot)/float(len(dates)))*100))
                url = None
                pageContent = None
                tree = None
                day = None
                month = None
                year = None
                if len(gameday.split('-')[2]) == 1:
                    day = '0'+gameday.split('-')[2]
                elif len(gameday.split('-')[2]) == 2:
                    day = gameday.split('-')[2]
                if len(gameday.split('-')[1]) == 1:
                    month = '0'+gameday.split('-')[1]
                elif len(gameday.split('-')[1]) == 2:
                    month = gameday.split('-')[1]
                year = gameday.split('-')[0]
                url = 'http://www.scoresandodds.com/grid_%s%s%s.html' % (year, month, day)
                pageContent=requests.get(url)
                tree = html.fromstring(pageContent.content)    
                for sport in range(1, 10):                    
                    root = '/html/body/div[1]/table/tr/td/div[2]/div[1]/div[1]/table/tr[1]/td[1]/div[%s]' % (sport)
                    sportpath = root+'/div[5]/div[1]/text()'
                    if len(tree.xpath(sportpath)) > 0 and tree.xpath(sportpath)[0] == 'NCAA BB':
                        team1root = '/div[6]/div[1]/table/tbody/tr[@class = "team odd"]'
                        team2root = '/div[6]/div[1]/table/tbody/tr[@class = "team even"]'
                        nameroot = '/td[1]/a/text()'
                        namepath1 = None
                        namepath2 = None
                        team1namelist = None
                        team2namelist = None
                        team1overunderlist = None
                        team2overunderlist = None
                        team1linelist = None
                        team2linelist = None
                        team1moneylinelist = None
                        team2moneylinelist = None
                        team1scorelist = None
                        team2scorelist = None
            
                        namepath1 = root+team1root+nameroot
                        namepath2 = root+team2root+nameroot
                        
                        team1namelist = tree.xpath(namepath1)
                        team2namelist = tree.xpath(namepath2)
            
                        team1linelist = []
                        for l1 in range(1, len(team1namelist)+1):
                            lpath1 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team odd"][position()=%s]/td[4]/text()' % (l1)
                            try:
                                team1linelist.append(tree.xpath(lpath1)[0])
                            except IndexError:
                                if tree.xpath(lpath1) == []:
                                    team1linelist.append(None)
                                                         
                        team2linelist = []
                        for l2 in range(1, len(team2namelist)+1):
                            lpath2 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team even"][position()=%s]/td[4]/text()' % (l2)
                            try:
                                team2linelist.append(tree.xpath(lpath2)[0])
                            except IndexError:
                                if tree.xpath(lpath2) == []:
                                    team2linelist.append(None)            
                        
                        team1overunderlist = []
                        for ou1 in range(1, len(team1namelist)+1):
                            oupath1 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team odd"][position()=%s]/td[4]/text()' % (ou1)
                            try:
                                team1overunderlist.append(tree.xpath(oupath1)[0])
                            except IndexError:
                                if tree.xpath(oupath1) == []:
                                    team1overunderlist.append('Null')
                        
                        team2overunderlist = []
                        for ou2 in range(1, len(team2namelist)+1):
                            oupath2 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team even"][position()=%s]/td[4]/text()' % (ou2)
                            try:
                                team2overunderlist.append(tree.xpath(oupath2)[0])
                            except IndexError:
                                if tree.xpath(oupath2) == []:
                                    team2overunderlist.append('Null')     
                        
                        team1scorelist = []
                        for s1 in range(1, len(team1namelist)+1):
                            spath1 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team odd"][position()=%s]/td[7]/span[1]/text()' % (s1)
                            try:
                                team1scorelist.append(tree.xpath(spath1)[0])
                            except IndexError:
                                if tree.xpath(spath1) == []:
                                    team1scorelist.append('Null')
            
                        team2scorelist = []            
                        for s2 in range(1, len(team2namelist)+1):
                            spath2 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team even"][position()=%s]/td[7]/span[1]/text()' % (s2)
                            try:
                                team2scorelist.append(tree.xpath(spath2)[0])
                            except IndexError:
                                if tree.xpath(spath2) == []:
                                    team2scorelist.append('Null')
                                    
                        team1moneylinelist = []
                        for ml1 in range(1, len(team1namelist)+1):
                            mlpath1 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team odd"][position()=%s]/td[5]/text()' % (ml1)
                            try:
                                team1moneylinelist.append(tree.xpath(mlpath1)[0])
                            except IndexError:
                                team1moneylinelist.append('Null')
                        team2moneylinelist = []
                        for ml2 in range(1, len(team2namelist)+1):
                            mlpath2 = root+'/div[6]/div[1]/table/tbody/tr[@class = "team even"][position()=%s]/td[5]/text()' % (ml2)
                            try:
                                team2moneylinelist.append(tree.xpath(mlpath2)[0])
                            except IndexError:
                                team2moneylinelist.append('Null')
                        if len(team1namelist) == len(team2namelist) == len(team2moneylinelist) == len(team1moneylinelist) == len(team1scorelist) == len(team2scorelist) == len(team1linelist) == len(team2linelist) == len(team1overunderlist) == len(team2overunderlist): 
                            for each in range(0, len(team1namelist)):
                                try:
                                    fbsgame = 'yes'
                                    favorite = None
                                    line = None
                                    team1 = None
                                    team2 = None
                                    moneyline1 = None
                                    moneyline2 = None
                                    score1 = None
                                    score2 = None
                                    linejuice = None
                                    overunder = None
                                    overunderjuice = None
                                    game = []
                                    
                                    try:
                                        team1 = oddsteamsdict[team1namelist[each][4:].upper()]
                                    except KeyError:
                                        if team1namelist[each][4:].upper() not in nond1:
                                            print(team1namelist[each][4:].upper())
                                            print(url)
                                        fbsgame = 'no'
                                        pass
                                    try:
                                        team2 = oddsteamsdict[team2namelist[each][4:].upper()]
                                    except KeyError:
                                        if team2namelist[each][4:].upper() not in nond1:
                                            print(team2namelist[each][4:].upper())
                                            print(url)
                                        fbsgame = 'no'
                                        pass
        
                                    if fbsgame == 'yes':                                
                                        try:
                                            moneyline1 = float(team1moneylinelist[each])
                                        except ValueError:
                                            if team1moneylinelist[each] == 'Null':
                                                moneyline1 = team1moneylinelist[each]
                                        try:
                                            moneyline2 = float(team2moneylinelist[each])
                                        except ValueError:
                                            if team2moneylinelist[each] == 'Null':
                                                moneyline2 = team2moneylinelist[each]
                                        try:
                                            score1 = int(team1scorelist[each])
                                        except ValueError:
                                            if team1scorelist[each] == 'Null':
                                                score1 = team1scorelist[each]
                                        try:
                                            score2 = int(team2scorelist[each])
                                        except ValueError:
                                            if team2scorelist[each] == 'Null':
                                                score2 = team2scorelist[each]
                                        favorite1 = False
                                        favorite2 = False
                                        x1 = None
                                        x2 = None
                                        y1 = None
                                        y2 = None
                                        spacesplit1 = None
                                        osplit1 = None
                                        usplit1 = None
                                        
                                        if team1linelist[each] == None and team2linelist[each] == None:
                                            x1 = 'Null'
                                            x2 = 'Null'
                                            y1 = 'Null'
                                            y2 = 'Null'
                                            favorite1 = True
                                        elif team1linelist[each] == None and team2linelist[each] != None:
                                            favorite2 = True
                                            x1 = 'Null'
                                            y1 = 'Null'
                                            try:
                                                x2 = float(team2linelist[each].strip().split(' ')[0])
                                            except ValueError:
                                                if team2linelist[each].strip().split(' ')[0] == 'PK':
                                                    x2 = 0
                                                    favorite2 = True                                          
                                            try:    
                                                y2 = float(team2linelist[each].strip().split(' ')[1])
                                            except IndexError:
                                                y2 = 0
                                            except ValueError:
                                                if team2linelist[each].strip().split(' ')[1] == 'EVEN':
                                                    y2 = 0   
                                        elif team2linelist[each] == None and team1linelist[each] != None:
                                            favorite1 = True
                                            try:
                                                x1 = float(team1linelist[each].strip().split(' ')[0])
                                            except ValueError:
                                                if team1linelist[each].strip().split(' ')[0] == 'PK':
                                                    x1 = 0
                                                    favorite1 = True                                       
                                            try:
                                                y1 = float(team1linelist[each].strip().split(' ')[1])
                                            except IndexError:
                                                y1 = 0
                                            except ValueError:
                                                if team1linelist[each].strip().split(' ')[1] == 'EVEN':
                                                    y1 = 0                                        
                                            x2 = 'Null'
                                            y2 = 'Null'
                                        elif team1linelist[each] != None and team2linelist[each] != None:                           
                                            spacesplit1 = team1linelist[each].strip().split(' ')
                                            osplit1 = team1linelist[each].strip().split('o')
                                            usplit1 = team1linelist[each].strip().split('u')
                                            
                                            if len(spacesplit1) == len(osplit1) == len(usplit1) == 1:
                                                try:
                                                    x1 = float(team1linelist[each].strip())
                                                except ValueError:
                                                    if team1linelist[each].strip() == 'PK':
                                                        x1 = 0
                                                        favorite1 = True
                                                y1 = 0
                                            elif len(spacesplit1) == 1 and len(osplit1) == 1 and len(usplit1) == 2:
                                                x1 = float(team1linelist[each].strip().split('u')[0])
                                                favorite2 = True
                                                y1 = float(team1linelist[each].strip().split('u')[1])
                                            elif len(spacesplit1) == 1 and len(osplit1) == 2 and len(usplit1) == 1:
                                                x1 = float(team1linelist[each].strip().split('o')[0])
                                                favorite2 = True
                                                y1 = float(team1linelist[each].strip().split('o')[1]) * -1  
                                            elif len(spacesplit1) == 2 and len(osplit1) == 1 and len(usplit1) == 1:
                                                try:
                                                    x1 = float(team1linelist[each].strip().split(' ')[0])
                                                    favorite1 = True
                                                except ValueError:
                                                    if team1linelist[each].strip().split(' ')[0] == 'PK':
                                                        x1 = 0
                                                        favorite1 = True
                                                try:
                                                    y1 = float(team1linelist[each].strip().split(' ')[1])
                                                except ValueError:
                                                    if team1linelist[each].strip().split(' ')[1] == 'EVEN':
                                                        y1 = 0
                
                                            spacesplit2 = team2linelist[each].strip().split(' ')
                                            osplit2 = team2linelist[each].strip().split('o')
                                            usplit2 = team2linelist[each].strip().split('u')                                        
                                            if len(spacesplit2) == len(osplit2) == len(usplit2) == 1:
                                                try:
                                                    x2 = float(team2linelist[each].strip())
                                                except ValueError:
                                                    if team2linelist[each].strip() == 'PK':
                                                        x2 = 0
                                                        favorite2 = True
                                                y2 = 0
                                            elif len(spacesplit2) == 1 and len(osplit2) == 1 and len(usplit2) == 2:
                                                x2 = float(team2linelist[each].strip().split('u')[0])
                                                favorite1 = True
                                                y2 = float(team2linelist[each].strip().split('u')[1])
                                            elif len(spacesplit2) == 1 and len(osplit2) == 2 and len(usplit2) == 1:
                                                x2 = float(team2linelist[each].strip().split('o')[0])
                                                favorite1 = True
                                                y2 = float(team2linelist[each].strip().split('o')[1])      
                                            elif len(spacesplit2) == 2 and len(osplit2) == 1 and len(usplit2) == 1:
                                                try:
                                                    x2 = float(team2linelist[each].strip().split(' ')[0])
                                                    favorite2 = True
                                                except ValueError:
                                                    if team2linelist[each].strip().split(' ')[0] == 'PK':
                                                        x2 = 0
                                                        favorite2 = True
                                                try:
                                                    y2 = float(team2linelist[each].strip().split(' ')[1])
                                                except ValueError:
                                                    if team2linelist[each].strip().split(' ')[1] == 'EVEN':
                                                        y2 = 0   
        
                                        if favorite1 == favorite2 == True:
                                            pass
                                        elif favorite1 == True and favorite2 == False:
                                            favorite = 1
                                            try:
                                                line = float(x1)
                                            except ValueError:
                                                if x1 == 'Null':
                                                    line = str(x1)
                                            try:
                                                linejuice = float(y1)
                                            except ValueError:
                                                if y1 == 'Null':
                                                    linejuice = str(y1)
                                            try:
                                                overunder = float(x2)
                                            except ValueError:
                                                if x2 == 'Null':
                                                    overunder = str(x2)
                                            try:
                                                overunderjuice = float(y2) 
                                            except ValueError:
                                                if y2 == 'Null':
                                                    overunderjuice = str(y2)                                
                                        elif favorite1 == False and favorite2 == True:
                                            favorite = 2
                                            try:
                                                line = float(x2)
                                            except ValueError:
                                                if x2 == 'Null':
                                                    line = str(x2)
                                            try:
                                                linejuice = float(y2)
                                            except ValueError:
                                                if y2 == 'Null':
                                                    linejuice = str(y2)
                                            try:
                                                overunder = float(x1)
                                            except ValueError:
                                                if x1 == 'Null':
                                                    overunder = str(x1)
                                            try:
                                                overunderjuice = float(y1) 
                                            except ValueError:
                                                if y1 == 'Null':
                                                    overunderjuice = str(y1)
                                        elif favorite1 == favorite2 == False:
                                            if x1 < 0:
                                                favorite = 1
                                                try:
                                                    line = float(x1)
                                                except ValueError:
                                                    if x1 == 'Null':
                                                        line = str(x1)
                                                try:
                                                    linejuice = float(y1)
                                                except ValueError:
                                                    if y1 == 'Null':
                                                        linejuice = str(y1)
                                                try:
                                                    overunder = float(x2)
                                                except ValueError:
                                                    if x2 == 'Null':
                                                        overunder = str(x2)
                                                try:
                                                    overunderjuice = float(y2) 
                                                except ValueError:
                                                    if y2 == 'Null':
                                                        overunderjuice = str(y2)                                   
                                            elif x2 < 0:
                                                favorite = 2
                                                try:
                                                    line = float(x2)
                                                except ValueError:
                                                    if x2 == 'Null':
                                                        line = str(x2)
                                                try:
                                                    linejuice = float(y2)
                                                except ValueError:
                                                    if y2 == 'Null':
                                                        linejuice = str(y2)
                                                try:
                                                    overunder = float(x1)
                                                except ValueError:
                                                    if x1 == 'Null':
                                                        overunder = str(x1)
                                                try:
                                                    overunderjuice = float(y1) 
                                                except ValueError:
                                                    if y1 == 'Null':
                                                        overunderjuice = str(y1) 
                                        if favorite == 1:
                                            game = [gameday, team1, team2, line, linejuice, overunder, overunderjuice, moneyline1, moneyline2, score1, score2, 1]
                                        elif favorite == 2:
                                            game = [gameday, team2, team1, line, linejuice, overunder, overunderjuice, moneyline2, moneyline1, score2, score1, 0]
                                        if favorite == None:
                                            favorite_errors.append(url)
                                        else:
                                            all_games.append(game)
                                            oddsinsert = []
                                            oddsinsertx = None
                                            oddslist = []
                                            initialoddsinsert = None
                                            add_odds = None
                                            oddsinsert.append("('"+game[0]+"', '"+str(game[1])+"', '"+str(game[2])+"', "+str(game[3])+", "+str(game[4])+", "+str(game[5])+", "+str(game[6])+", "+str(game[7])+", "+str(game[8])+", "+str(game[9])+", "+str(game[10])+", "+str(game[11])+")")
                                            oddsinsertx = ','.join(oddsinsert)
                                            oddslist = ['INSERT INTO future_games VALUES', oddsinsertx, ';']
                                            initialoddsinsert = ' '.join(oddslist)  
                                            add_odds = initialoddsinsert  
                                            cursor.execute('SET foreign_key_checks = 0;')
                                            try:
                                                cursor.execute(add_odds)
                                                cnx.commit()
                                            except DataError:
                                                print('Error Loading %s' % (add_odds))
                                            cursor.execute('SET foreign_key_checks = 1;')
                                except IntegrityError:
                                    pass
                        else:
                            error = (team1namelist[each][4:], team2namelist[each][4:])
                            nonfbsteams.append(error)
        
                    else:
                        all_errors.append(url) 
        cursor = cnx.cursor() 
        cursor.execute('SET SQL_SAFE_UPDATES = 0;')
        cursor.execute('DELETE FROM ncaa_bb.future_games WHERE favscore is not NULL or line is NULL;')
        cursor.execute('SET SQL_SAFE_UPDATES = 1;')
        cnx.commit()
    
        cursor.close()
        cnx.close() 
    print('Updated Future NCAA Basketball Odds to %s' % (str(start_date)))
