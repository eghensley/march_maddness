import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
sys.path.insert(-1, os.path.join(cur_path, 'model_conf'))
sys.path.insert(-1, cur_path)


def update(cnx):
    import requests
    from lxml import html
    import datetime
    import pandas as pd
    from mysql.connector import IntegrityError    
    
    print('Starting NCAA Basketball Stats Update')   
    teamstats = ['points-per-game', 'offensive-efficiency', 'floor-percentage', 'points-from-2-pointers', 'points-from-3-pointers', 
                 'percent-of-points-from-2-pointers', 'percent-of-points-from-3-pointers', 'percent-of-points-from-free-throws', 
                 'defensive-efficiency', 'shooting-pct', 'fta-per-fga', 'ftm-per-100-possessions', 'free-throw-rate', 
                 'three-point-rate', 'two-point-rate', 'three-pointers-made-per-game', 'effective-field-goal-pct', 'true-shooting-percentage', 
                 'offensive-rebounds-per-game', 'offensive-rebounding-pct', 'defensive-rebounds-per-game',
                 'defensive-rebounding-pct', 'blocks-per-game', 'steals-per-game', 'block-pct', 'steals-perpossession', 'steal-pct',
                 'assists-per-game', 'turnovers-per-game', 'turnovers-per-possession', 'assist--per--turnover-ratio', 'assists-per-fgm', 'assists-per-possession',
                 'turnover-pct', 'personal-fouls-per-game', 'personal-fouls-per-possession', 'personal-foul-pct', 
                 'possessions-per-game', 'extra-chances-per-game', 'effective-possession-ratio']
     
    cursor = cnx.cursor()
    cursor.execute('select max(statdate) from basestats')
    x = cursor.fetchall()
    cursor.execute('Select oddsdate, favorite, underdog from ncaa_bb.oddsdata where oddsdate >= "%s-%s-%s" order by oddsdate asc;'% (x[0][0].year, x[0][0].month, x[0][0].day))
    inputs = pd.DataFrame(cursor.fetchall())
    cursor.close()
    if len(inputs) > 0:
        alldates = inputs[0]
        alldates = alldates.drop_duplicates()
        

        cursor = cnx.cursor()
        
        progress = 0
        for usedate in alldates:
            progress += 1
        
            print('%.2f percent complete' % (float(progress) / float(len(alldates)) * 100))    
            statsdata = pd.DataFrame(columns = teamstats)
            whichteams = None
            whichteams = list(inputs[inputs[0] == usedate][1])
            whichteams = whichteams + list(inputs[inputs[0] == usedate][2])
            statsdata['teamname'] = whichteams
            urldate = str((usedate + datetime.timedelta(days=1)).year) + '-' + str((usedate + datetime.timedelta(days=1)).month) + '-' + str((usedate + datetime.timedelta(days=1)).day)
            for each in teamstats:
                tree = None
                url = None
                url = 'https://www.teamrankings.com/ncaa-basketball/stat/%s?date=%s' % (each, urldate)
                pageContent=requests.get(url)
                tree = html.fromstring(pageContent.content)
                lastgame = []
                for team in whichteams:
                    value = None
                    formattedvalue = None
                    try:
                        value = tree.xpath('//tbody/tr[td[2]/a/text()="%s"]/td[@class="text-right"][3]/text()' % (team))[0]
                    except IndexError:
                        value = '--'
                    try:
                        formattedvalue = float(value)
                    except ValueError:
                        if value[-1] == '%':
                            formattedvalue = float(value[:-1])
                        elif value  == '--':
                            formattedvalue = 'NULL'
                    lastgame.append(formattedvalue)
                statsdata[each] = lastgame
            
            for team in whichteams:
                sqldata = []
                for label in teamstats:
                    sqldata.append(str(statsdata['%s' % label][statsdata.teamname == team].values[0]))
                sqldata = ', '.join(sqldata)
                sqldata = 'INSERT INTO ncaa_bb.basestats VALUES ("%s", "%s", ' % (team, usedate) + sqldata + ');'
                try:
                    cursor.execute(sqldata)
                    cnx.commit()
                except IntegrityError:
                    pass
        cursor.close()
        cnx.close()
    print('Updated NCAA Basketball Stats to %s' % (str(x[0][0])))
