from typing import Optional
from fastapi import FastAPI
import uvicorn
import requests
import json
import pandas as pd
import numpy as np
import os

app = FastAPI()

@app.get("/{hero_name}")#menunjukkan cara bermain lane category dan times category terbaik berdasarkan win rate dan heroes yang dipilih agar pengguna mengetahui cara bermain hero yang benar dan waktu terbaik memainkan hero tersebut
def read_heroes(hero_name: str):
	df_heroes = pd.DataFrame()
	df_lane = pd.DataFrame()
	data_h = requests.get("https://api.opendota.com/api/heroes")
	data_l = requests.get("https://api.opendota.com/api/scenarios/laneRoles")
	data_heroes = json.loads(data_h.text)
	data_lane = json.loads(data_l.text)
	#GETTING HEROES DATA
	for p in range(len(data_heroes)):
		df_heroes = df_heroes.append({'Id':data_heroes[p]["id"],'Name':data_heroes[p]["localized_name"],'Attribute':data_heroes[p]["primary_attr"],'Roles':data_heroes[p]["roles"]}, ignore_index=True)
	#GETTING MATCH DATA
	for p in range(len(data_lane)):
		df_lane = df_lane.append({'Hero_Id':data_lane[p]["hero_id"],'Lane_role':data_lane[p]["lane_role"],'Times':data_lane[p]["time"],'Games':data_lane[p]["games"],'Win':data_lane[p]["wins"]}, ignore_index=True)
	#CATEGORY TIMES
	times_conditions = [
	(df_lane['Times'] <= 900),#kurang dari atau sama dengan 15 menit termasuk early game
	(df_lane['Times'] > 900) & (df_lane['Times'] <= 2700),#kurang dari atau sama dengan 45 menit termasuk mid game
	(df_lane['Times'] > 2700)#lebih dari 45 menit match termasuk late game
	]
	times_values = ['Early Game', 'Mid Game', 'Late Game'] 
	df_lane['Times_Category'] = np.select(times_conditions, times_values)
	#LANE ROLE CATEGORY
	lane_conditions = [
	(df_lane['Lane_role'] == 1.0),
	(df_lane['Lane_role'] == 2.0),
	(df_lane['Lane_role'] == 3.0),
	(df_lane['Lane_role'] == 4.0),
	]
	lane_values = ['Safe', 'Mid', 'Off','Jungle'] 
	df_lane['Lane_Category'] = np.select(lane_conditions, lane_values)
	#WIN RATE
	df_lane['Win_Rate']=round(pd.to_numeric(df_lane['Win'])/pd.to_numeric(df_lane['Games'])*100,2)

	id_hero_dipilih = df_heroes[df_heroes['Name'].str.lower()==hero_name.lower()]
	
	lane = df_lane[df_lane['Hero_Id']==id_hero_dipilih['Id'].iloc[0]].groupby(['Lane_Category','Times_Category'])[['Win_Rate']].mean()
	
	lane = lane.reset_index()
	lane = lane.sort_values(by='Win_Rate', ascending=False)
	
	new_lane = pd.DataFrame()
	for p in range(len(lane)):
	    new_lane = new_lane.append({'Lane_Category':lane['Lane_Category'].iloc[p],'Times_Category':lane['Times_Category'].iloc[p],'Win_Rate':lane['Win_Rate'].iloc[p]}, ignore_index=True)
	results = new_lane.to_json(orient="index")
	parsed = json.loads(results)						
	return parsed

@app.get("/")#ranking hero terbaik berdasarkan win rate untuk digunakan dalam game
def read_best():
	df_heroes = pd.DataFrame()
	df_lane = pd.DataFrame()
	data_h = requests.get("https://api.opendota.com/api/heroes")
	data_l = requests.get("https://api.opendota.com/api/scenarios/laneRoles")
	data_heroes = json.loads(data_h.text)
	data_lane = json.loads(data_l.text)
	#GETTING HEROES DATA
	for p in range(len(data_heroes)):
		df_heroes = df_heroes.append({'Hero_Id':data_heroes[p]["id"],'Name':data_heroes[p]["localized_name"],'Attribute':data_heroes[p]["primary_attr"],'Roles':data_heroes[p]["roles"]}, ignore_index=True)
	#GETTING MATCH DATA
	for p in range(len(data_lane)):
		df_lane = df_lane.append({'Hero_Id':data_lane[p]["hero_id"],'Lane_role':data_lane[p]["lane_role"],'Times':data_lane[p]["time"],'Games':data_lane[p]["games"],'Win':data_lane[p]["wins"]}, ignore_index=True)
	#WIN RATE
	df_lane['Win_Rate']=round(pd.to_numeric(df_lane['Win'])/pd.to_numeric(df_lane['Games'])*100,2)
	df_gabungan = pd.merge(df_lane, df_heroes, on='Hero_Id', how='inner')
	lane = df_gabungan.groupby('Name')[['Win_Rate']].mean()
	lane = lane.reset_index()
	rank = lane.sort_values(by='Win_Rate', ascending=False)
	rank['Rank'] = list(range(1,len(lane.sort_values(by='Win_Rate', ascending=False).index)+1))
	
	results = rank.sort_values(by='Win_Rate', ascending=False).to_json(orient="index")
	parsed = json.loads(results)						
	return parsed
if __name__== "__main__":
	uvicorn.run(app,host="0.0.0.0",port=int(os.environ.get('PORT',5000)), log_level="info")
