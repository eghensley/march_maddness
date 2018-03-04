import os, sys
try:                                            # if running in CLI
    cur_path = os.path.abspath(__file__)
except NameError:                               # if running in IDE
    cur_path = os.getcwd()
while cur_path.split('/')[-1] != 'bb_preds':
    cur_path = os.path.abspath(os.path.join(cur_path, os.pardir))
sys.path.insert(-1, os.path.join(cur_path, 'model_conf'))

import bb_odds
import bb_stats
import gamedata
import mongodb_weighted_stat_insert
import mongo_stat_insert
import _config
from pymongo import MongoClient
import mysql.connector 
import fourfeats_elo
import derived_insert
import vegas_pred_insert
import predictor_insert
import bb_future_odds
import mongodb_weighted_stat_insert_optimized

def mysql_client():
    sql = mysql.connector.connect(user='root', password=_config.mysql_creds,host='127.0.0.1',database='ncaa_bb')
    return sql
try:
    mongodb_client = MongoClient(_config.mongodb_creds)
except:
    mongodb_client = MongoClient()

cnx = mysql_client()

def run():
    bb_odds.update(mysql_client() )
    bb_future_odds.update(mysql_client())
    bb_stats.update(mysql_client() )
    gamedata.update(mysql_client() )
#    for od in ['possessions', 'target', 'offensive_stats', 'defensive_stats']:
#        for sa in ['pts_scored', 'pts_allowed']:
#            mongodb_weighted_stat_insert_optimized.insert(od, sa, mongodb_client, mysql_client())
#            mongo_stat_insert.update(od, sa, mongodb_client, mysql_client())
#    fourfeats_elo.update(mongodb_client, mysql_client())  
#    derived_insert.update()
#    vegas_pred_insert.update()
#    predictor_insert.update()

if __name__ == '__main__':
    run()
