import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
sys.path.insert(-1, cur_path)


import pandas as pd
import mysql.connector 
import numpy as np
from datetime import datetime
import _config

cnx = mysql.connector.connect(user='root', password=_config.mysql_creds,
                              host='127.0.0.1',
                              database='ncaa_bb') 
def pull_index():
    cursor = cnx.cursor()
    query = 'SELECT teamname, date FROM ncaa_bb.gamedata order by date ASC, teamname ASC;'
    labels = ['teamname', 'date']
    cursor.execute(query)
    gamedata = pd.DataFrame(cursor.fetchall(), columns = labels)
    return gamedata
    
def team_rolling_avg_weighted(stat, length, start_date):   

    cursor = cnx.cursor()
    if len(stat.split('`/`')) == 1:
        query = "SELECT \
                oddsdate, favorite, underdog, bs1.`%s`, bs2.`%s`, homeaway\
                FROM\
                oddsdata as od\
                join basestats as bs1 on od.oddsdate = bs1.statdate and bs1.teamname = od.favorite\
                join basestats as bs2 on od.oddsdate = bs2.statdate and bs2.teamname = od.underdog\
                ORDER BY oddsdate ASC" % (stat, stat)
    elif len(stat.split('`/`')) == 2:
        query = "SELECT \
                oddsdate, favorite, underdog, bs1.`%s`, bs2.`%s`, homeaway\
                FROM\
                oddsdata as od\
                join basestats as bs1 on od.oddsdate = bs1.statdate and bs1.teamname = od.favorite\
                join basestats as bs2 on od.oddsdate = bs2.statdate and bs2.teamname = od.underdog\
                ORDER BY oddsdate ASC" % ('/bs1.'.join(stat.split('/')), '/bs2.'.join(stat.split('/')))        

    cursor.execute(query)
    names = ['date', 'fav', 'dog', 'favstat', 'dogstat', 'ha']
    data = pd.DataFrame(cursor.fetchall(), columns = names)
    data=data.dropna(how='any')
    cursor.close()
    
    fordict = {}
    againstdict = {}
    alloweddict = {}
    scoredict = {}
    
    for date, t1, t2, s1, s2, loc in np.array(data):
        if s1 == s1 and s2 == s2:
            t1_current_allow = None
            t2_current_allow = None
            t1_current_score = None
            t2_current_score = None
            
            t1_weighted_score = None
            t2_weighted_score = None
            t1_weighted_allowed = None
            t2_weighted_allowed = None
            
            avg_allow = None
            avg_score = None
            
            try:
                t1_current_allow = alloweddict[t1]
            except KeyError:
                t1_current_allow = False
            try:
                t2_current_allow = alloweddict[t2]
            except KeyError:
                t2_current_allow = False
        
            try:
                t1_current_score = scoredict[t1]
            except KeyError:
                t1_current_score= False
        
            try:
                t2_current_score = scoredict[t2]
            except KeyError:
                t2_current_score = False


            if np.mean(t1_current_score) == 0 or np.mean(t2_current_score) == 0:
                avg_score = []
                for each in scoredict.values():
                    avg_score.append(np.mean(each))
                if len(avg_score) > 0:
                    avg_score = np.mean(avg_score)
                else:
                    avg_score = np.mean(list(data['favstat']) + list(data['dogstat']))
            if np.mean(t1_current_allow) == 0 or np.mean(t2_current_allow) == 0:
                avg_allow = []
                for each in alloweddict.values():
                    avg_allow.append(np.mean(each))
                if len(avg_allow) > 0:
                    avg_allow = np.mean(avg_allow)  
                else:
                    avg_allow = np.mean(list(data['favstat']) + list(data['dogstat']))
                
            if not t2_current_allow:
                t1_weighted_score = 'NULL'
            else:
                if np.mean(t2_current_allow) == 0:
                    t1_weighted_score = s1/avg_allow
                else:
                    t1_weighted_score = s1/np.mean(t2_current_allow)
            if not t1_current_allow:
                t2_weighted_score = 'NULL'
            else:
                if np.mean(t1_current_allow) == 0:
                    t2_weighted_score = s2/avg_allow
                else:
                    t2_weighted_score = s2/np.mean(t1_current_allow)
                      
        
            if not t2_current_score:
                t1_weighted_allowed = 'NULL'
            else:
                if np.mean(t2_current_score) == 0:
                    t1_weighted_allowed = s1/avg_score
                else:
                    t1_weighted_allowed = s1/np.mean(t2_current_score)
            if not t1_current_score:
                t2_weighted_allowed = 'NULL'
            else:
                if np.mean(t1_current_score) == 0:
                    t2_weighted_allowed = s2/avg_score
                else:
                    t2_weighted_allowed = s2/np.mean(t1_current_score)
                    
            if datetime.strptime(start_date, '%Y-%m-%d').date() <= date:               
                fordict[str(date)+t1.replace(' ', '_')] = {'date':date, 'team':t1, '%s_g_Tweight_for_%s'%(length, stat):t1_weighted_score}
                fordict[str(date)+t2.replace(' ', '_')] = {'date':date, 'team':t2, '%s_g_Tweight_for_%s'%(length, stat):t2_weighted_score}
                againstdict[str(date)+t1.replace(' ', '_')] = {'date':date, 'team':t1, '%s_g_Tweight_allow_%s'%(length, stat):t1_weighted_allowed}
                againstdict[str(date)+t2.replace(' ', '_')] = {'date':date, 'team':t2, '%s_g_Tweight_allow_%s'%(length, stat):t2_weighted_allowed}                  
                    
            if not t1_current_allow:
                t1_current_allow = [s2]
            else:
                t1_current_allow.append(s2)
            if not t1_current_score:
                t1_current_score = [s1]
            else:
                t1_current_score.append(s1)        
        
            if not t2_current_score:
                t2_current_score = [s2]
            else:
                t2_current_score.append(s2)
            if not t2_current_allow:
                t2_current_allow = [s1]
            else:
                t2_current_allow.append(s1) 
            
            if t1_current_allow and len(t1_current_allow) > length:
                t1_current_allow = t1_current_allow[len(t1_current_allow)-(length):]
            if t2_current_allow and len(t2_current_allow) > length:
                t2_current_allow = t2_current_allow[len(t2_current_allow)-(length):]
            if t1_current_score and len(t1_current_score) > length:
                t1_current_score = t1_current_score[len(t1_current_score)-(length):]
            if t2_current_score and len(t2_current_score) > length:
                t2_current_score = t2_current_score[len(t2_current_score)-(length):]    
    
            if len(t2_current_score) != len(t2_current_allow):
                print('team 2 mismatch')
                break
            if len(t1_current_score) != len(t1_current_allow):
                print('team 1 mismatch')
                break    
            if len(t2_current_score) > length:
                print('team 2 over 5')
                break
            if len(t1_current_score) > length:
                print('team 1 over 5')
                break  
            alloweddict[t1] = t1_current_allow
            alloweddict[t2] = t2_current_allow
            scoredict[t1] = t1_current_score
            scoredict[t2] = t2_current_score
    
    return fordict, againstdict

def ha_switch(in_num):
    if in_num == 0:
        return 1
    elif in_num == 1:
        return 0

def ha_rolling_avg_weighted(stat, length, start_date):
#    stat, length, start_date = 'defensive-rebounds-per-game', 5, '2018-02-27'
    import pandas as pd
    import numpy as np   
    from datetime import datetime

    cursor = cnx.cursor()
    if len(stat.split('`/`')) == 1:
        query = "SELECT \
                oddsdate, favorite, underdog, bs1.`%s`, bs2.`%s`, homeaway\
                FROM\
                oddsdata as od\
                join basestats as bs1 on od.oddsdate = bs1.statdate and bs1.teamname = od.favorite\
                join basestats as bs2 on od.oddsdate = bs2.statdate and bs2.teamname = od.underdog\
                ORDER BY oddsdate ASC" % (stat, stat)
    elif len(stat.split('`/`')) == 2:
        query = "SELECT \
                oddsdate, favorite, underdog, bs1.`%s`, bs2.`%s`, homeaway\
                FROM\
                oddsdata as od\
                join basestats as bs1 on od.oddsdate = bs1.statdate and bs1.teamname = od.favorite\
                join basestats as bs2 on od.oddsdate = bs2.statdate and bs2.teamname = od.underdog\
                ORDER BY oddsdate ASC" % ('/bs1.'.join(stat.split('/')), '/bs2.'.join(stat.split('/')))        
    cursor.execute(query)
    names = ['date', 'fav', 'dog', 'favstat', 'dogstat', 'ha']
    data = pd.DataFrame(cursor.fetchall(), columns = names)
    data=data.dropna(how='any')
    cursor.close()
    
    fordict = {}
    againstdict = {}
    alloweddict = {}
    scoredict = {}
    for date, t1, t2, s1, s2, loc in np.array(data):
        if s1 == s1 and s2 == s2:
            t1_current_allow = None
            t2_current_allow = None
            t1_current_score = None
            t2_current_score = None
            
            t1_weighted_score = None
            t2_weighted_score = None
            t1_weighted_allowed = None
            t2_weighted_allowed = None
            
            t1_ha_score_spread = None
            t1_ha_allow_spread = None
            t2_ha_score_spread = None
            t2_ha_allow_spread = None
            
            avg_allow = None
            avg_score = None
            
            try:
                t1_current_allow = alloweddict[t1][loc]
            except KeyError:
                t1_current_allow = False
                alloweddict[t1] = [False, False]
            try:
                t2_current_allow = alloweddict[t2][ha_switch(loc)]
            except KeyError:
                t2_current_allow = False
                alloweddict[t2] = [False, False]
        
            try:
                t1_current_score = scoredict[t1][loc]
            except KeyError:
                t1_current_score= False
                scoredict[t1] = [False, False]
                
            try:
                t2_current_score = scoredict[t2][ha_switch(loc)]
            except KeyError:
                t2_current_score = False
                scoredict[t2] = [False, False]
                
                
                
            if np.mean(t1_current_score) == 0 or np.mean(t2_current_score) == 0:
                avg_score = []
                for each in scoredict.values():
                    for every in each:
                        if every:
                            avg_score.append(np.mean(every))
                if len(avg_score) > 0:
                    avg_score = np.mean(avg_score)
                else:
                    avg_score = np.mean(list(data['favstat']) + list(data['dogstat']))
            if np.mean(t1_current_allow) == 0 or np.mean(t2_current_allow) == 0:
                avg_allow = []
                for each in alloweddict.values():
                    for every in each:
                        if every:
                            avg_allow.append(np.mean(every))
                if len(avg_allow) > 0:
                    avg_allow = np.mean(avg_allow) 
                else:
                    avg_allow = np.mean(list(data['favstat']) + list(data['dogstat']))
                    
            
            
            
            
            if not t2_current_allow:
                t1_weighted_score = 'NULL'
            else:
                if np.mean(t2_current_allow) == 0:
                    t1_weighted_score = s1/avg_allow
                else:
                    t1_weighted_score = s1/np.mean(t2_current_allow)
            if not t1_current_allow:
                t2_weighted_score = 'NULL'
            else:
                if np.mean(t1_current_allow) == 0:
                    t2_weighted_score = s2/avg_allow
                else:
                    t2_weighted_score = s2/np.mean(t1_current_allow)
                      
        
            if not t2_current_score:
                t1_weighted_allowed = 'NULL'
            else:
                if np.mean(t2_current_score) == 0:
                    t1_weighted_allowed = s1/avg_score
                else:
                    t1_weighted_allowed = s1/np.mean(t2_current_score)
            if not t1_current_score:
                t2_weighted_allowed = 'NULL'
            else:
                if np.mean(t1_current_score) == 0:
                    t2_weighted_allowed = s2/avg_score
                else:
                    t2_weighted_allowed = s2/np.mean(t1_current_score)        
            
            
            
            if t1_current_score and scoredict[t1][ha_switch(loc)]:
                try:
                    t1_ha_score_spread = np.mean(scoredict[t1][0]) - np.mean(scoredict[t1][1])
                except IndexError:
                    t1_ha_score_spread = 'NULL'
            else:
                t1_ha_score_spread = 'NULL'
        
            if t2_current_score and scoredict[t2][loc]:
                try:
                    t2_ha_score_spread = np.mean(scoredict[t2][0]) - np.mean(scoredict[t2][1])
                except IndexError:
                    t2_ha_score_spread = 'NULL'
            else:
                t2_ha_score_spread = 'NULL'
            
         
            
            if t1_current_allow and alloweddict[t1][ha_switch(loc)]:
                try:
                    t1_ha_allow_spread = np.mean(alloweddict[t1][0]) - np.mean(alloweddict[t1][1])
                except IndexError:
                    t1_ha_allow_spread = 'NULL'
            else:
                t1_ha_allow_spread = 'NULL'
        
            if t2_current_allow and alloweddict[t2][loc]:
                try:
                    t2_ha_allow_spread = np.mean(alloweddict[t2][0]) - np.mean(alloweddict[t2][1])
                except IndexError:
                    t2_ha_allow_spread = 'NULL'
            else:
                t2_ha_allow_spread = 'NULL' 
                
            if datetime.strptime(start_date, '%Y-%m-%d').date() <= date:
                fordict[str(date)+t1.replace(' ', '_')] = {'date':date, 'team':t1, '%s_g_HAweight_for_%s' % (length, stat):t1_weighted_score, '%s_g_HAspread_for_%s'%(length, stat): t1_ha_score_spread}
                fordict[str(date)+t2.replace(' ', '_')] = {'date':date, 'team':t2, '%s_g_HAweight_for_%s' % (length, stat):t2_weighted_score, '%s_g_HAspread_for_%s'%(length, stat): t2_ha_score_spread}
                againstdict[str(date)+t1.replace(' ', '_')] = {'date':date, 'team':t1, '%s_g_HAweight_allow_%s' % (length, stat):t1_weighted_allowed, '%s_g_HAspread_allow_%s'%(length, stat): t1_ha_allow_spread}
                againstdict[str(date)+t2.replace(' ', '_')] = {'date':date, 'team':t2, '%s_g_HAweight_allow_%s' % (length, stat):t2_weighted_allowed, '%s_g_HAspread_allow_%s'%(length, stat): t2_ha_allow_spread} 
            
            if not t1_current_allow:
                t1_current_allow = [s2]
            else:
                t1_current_allow.append(s2)
            if not t1_current_score:
                t1_current_score = [s1]
            else:
                t1_current_score.append(s1)        
        
            if not t2_current_score:
                t2_current_score = [s2]
            else:
                t2_current_score.append(s2)
            if not t2_current_allow:
                t2_current_allow = [s1]
            else:
                t2_current_allow.append(s1) 
            
            if t1_current_allow and len(t1_current_allow) > length:
                t1_current_allow = t1_current_allow[len(t1_current_allow)-(length):]
            if t2_current_allow and len(t2_current_allow) > length:
                t2_current_allow = t2_current_allow[len(t2_current_allow)-(length):]
            if t1_current_score and len(t1_current_score) > length:
                t1_current_score = t1_current_score[len(t1_current_score)-(length):]
            if t2_current_score and len(t2_current_score) > length:
                t2_current_score = t2_current_score[len(t2_current_score)-(length):]    
        
            if len(t2_current_score) != len(t2_current_allow):
                print('team 2 mismatch')
                break
            if len(t1_current_score) != len(t1_current_allow):
                print('team 1 mismatch')
                break    
            if len(t2_current_score) > length:
                print('team 2 over %s' % (length))
                break
            if len(t1_current_score) > length:
                print('team 1 over %' % (length))
                break  
            if loc == 0:
                scoredict[t1] = [t1_current_score, scoredict[t1][1]]
                alloweddict[t1] = [t1_current_allow, alloweddict[t1][1]]
                alloweddict[t2] = [alloweddict[t2][0], t2_current_allow]
                scoredict[t2] = [scoredict[t2][0], t2_current_score]
            else:
                alloweddict[t1] = [alloweddict[t1][0], t1_current_allow]
                scoredict[t1] = [scoredict[t1][0], t1_current_score]
                scoredict[t2] = [t2_current_score, scoredict[t2][1]]
                alloweddict[t2] = [t2_current_allow, alloweddict[t2][1]]        
    return fordict, againstdict
    
        
        
        
        