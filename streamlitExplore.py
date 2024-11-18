import pandas as pd
import streamlit as st
import warnings
warnings.filterwarnings("ignore")

data = pd.read_csv("/Users/asutoshdalei/Desktop/Work/GlobalTerrorism/globalterrorismdb.csv",encoding= 'ISO-8859-1',nrows=100)
data.rename(columns={'iyear':'Year','imonth':'Month','iday':'Day','country_txt':'Country','region_txt':'Region','attacktype1_txt':'AttackType','target1':'Target','nkill':'Killed','nwound':'Wounded','summary':'Summary','gname':'Group','targtype1_txt':'Target_type','weaptype1_txt':'Weapon_type','motive':'Motive'},inplace=True)

data=data[['Year','Month','Day','Country','Region','city','latitude','longitude','AttackType','Killed','Wounded','Target','Summary','Group','Target_type','Weapon_type','Motive']]
data['casualities']=data['Killed']+data['Wounded']

data = data[(data.Month!=0) & (data.Day!=0)]

def dateFnx(row):
    date = str(row['Month'])+':'+str(row['Day'])+':'+str(row['Year'])
    return pd.to_datetime(date,format='%m:%d:%Y')

data['date'] = data.apply(dateFnx,axis=1)




# Streamlit section

## Impact Map
st.title("Global Terrorism Impact")
mapData = data[data.latitude.notna() & data.longitude.notna()][['latitude','longitude']]
st.map(mapData)

## Year Cases
yearCount = data.groupby('Year')['Month'].count()
st.bar_chart(data=yearCount)

