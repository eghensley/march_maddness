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
    import pandas as pd
    import datetime
    print('Starting Game Data Update')
    cursor = cnx.cursor()
    cursor.execute('select max(gamedata.date) from ncaa_bb.gamedata')
    x = cursor.fetchall()
    x = [[x[0][0]+ datetime.timedelta(days=-1)]]
    
    query = 'select bs.teamname, bs.statdate, od.favorite, od.underdog, homeaway from basestats as bs join oddsdata as od on (bs.teamname = od.favorite OR bs.teamname = od.underdog) and bs.statdate = od.oddsdate where bs.statdate >= "%s-%s-%s"' % (x[0][0].year, x[0][0].month, x[0][0].day)
    cursor.execute(query)
    names = ['teamname', 'date', 'favorite', 'underdog', 'homeaway']
    data = pd.DataFrame(cursor.fetchall(), columns = names)

    query = 'select favorite, oddsdate, favorite, underdog, homeaway from future_games'
    cursor.execute(query)
    names = ['teamname', 'date', 'favorite', 'underdog', 'homeaway']
    fav_data = pd.DataFrame(cursor.fetchall(), columns = names)    

    query = 'select underdog, oddsdate, favorite, underdog, homeaway from future_games'
    cursor.execute(query)
    names = ['teamname', 'date', 'favorite', 'underdog', 'homeaway']
    dog_data = pd.DataFrame(cursor.fetchall(), columns = names) 
    
    data = data.append(dog_data)
    data = data.append(fav_data)
    data = data.reset_index()
    if len(data) > 0:
        data['opponent'] = [data['favorite'][i] if data['favorite'][i] != data['teamname'][i] else data['underdog'][i] for i in range(0, len(data['teamname']))]
        data['location'] = [data['teamname'][i] if data['homeaway'][i] == 1 else data['opponent'][i] for i in range(0, len(data['teamname']))]
        
        del data['favorite']
        del data['underdog']
        del data['homeaway']
        
        names = data['teamname']
        dates = data['date']
        opponents = data['opponent']
        locations = data['location']
        
        from mysql.connector import IntegrityError
        progress = 0
        for name, date, opponent, location in zip(names, dates, opponents, locations):
            progress += 1
            try:
                cursor.execute(('INSERT INTO ncaa_bb.gamedata VALUES ("%s", "%s", "%s", "%s"' % (name, date, opponent, location)) + ');')
                cnx.commit()
            except IntegrityError:
                pass
            print('%.2f percent complete' % (float(progress) / float(len(data)) * 100))    
    cursor.close()
    cnx.close()
    print('Completed NCAA Basketball Game Data Update')