import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import time
import os
import warnings
warnings.filterwarnings("ignore")



def dateFnx(row):
    date = str(row['Month'])+':'+str(row['Day'])+':'+str(row['Year'])
    return pd.to_datetime(date,format='%m:%d:%Y')


@st.cache_data
def fetch_and_clean_data(path,nrows = 10000):
    if nrows == -1:
        data = pd.read_csv(path,encoding= 'ISO-8859-1')
    else:
        data = pd.read_csv(path,encoding= 'ISO-8859-1',nrows=nrows)
    data.rename(columns={'iyear':'Year','imonth':'Month','iday':'Day','country_txt':'Country','region_txt':'Region','attacktype1_txt':'AttackType','target1':'Target','nkill':'Killed','nwound':'Wounded','summary':'Summary','gname':'Group','targtype1_txt':'Target_type','weaptype1_txt':'Weapon_type','motive':'Motive'},inplace=True)

    data=data[['Year','Month','Day','Country','Region','city','latitude','longitude','AttackType','Killed','Wounded','Target','Summary','Group','Target_type','Weapon_type','Motive']]
    data['casualities']=data['Killed']+data['Wounded']

    data = data[(data.Month!=0) & (data.Day!=0)]
    data['date'] = data.apply(dateFnx,axis=1)

    data['Weapon_type'].replace("Vehicle (not to include vehicle-borne explosives, i.e., car or truck bombs)","Vehicle",inplace=True)
    return data

data_path = "/Users/asutoshdalei/Desktop/Work/GlobalTerrorism/globalterrorismdb.csv"
data = fetch_and_clean_data(data_path,nrows= -1)

countryWise = data.groupby('Country')['casualities'].sum()
countryList = countryWise[countryWise>5].index.tolist()

# Streamlit section
st.title("Analysis of Global Terrorism")

minTime,maxTime = data[data.latitude.notna() & data.longitude.notna()]['date'].agg(['min','max'])
dateRangeOptions = pd.date_range(minTime,maxTime,freq = 'W').strftime('%Y-%m-%d').tolist()
start_time,end_time = st.select_slider(label='Date Range',options=dateRangeOptions,value=(dateRangeOptions[0],dateRangeOptions[-1]))


## Sidebar
with st.sidebar:
    st.title("Analysis of Global Terrorism")
    imgPath = '/Users/asutoshdalei/Desktop/Work/GlobalTerrorism/terrorismlogo.jpg'
    st.image(imgPath)

    mapFlagCol = st.radio(label="Geography:",options=['Region','Country'])
    variable_radio = st.radio(label="Analysis Measure:",options=['Attacks','Casualities'])
    
    if mapFlagCol == 'Region':
        mapSelection = st.multiselect(label='Select Region',options = data.Region.unique().tolist()+['Global'],default='Global')
        if ('Global' in mapSelection) or (mapSelection==[]):
            mapSelection = data.Region.unique().tolist()
    else:
        mapSelection = st.multiselect(label='Select Country',options = data.Country.unique().tolist()+['Global'],default='Global')
        if ('Global' in mapSelection) or (mapSelection==[]):
            mapSelection = data.Country.unique().tolist()
    
    mapData = data[data.latitude.notna() & data.longitude.notna() & data[mapFlagCol].isin(mapSelection) & (data['date']>=start_time) & (data['date']<=end_time)]
    
    col1, col2 = st.columns(2)
    pctChangeAtt = mapData.groupby('Year')['casualities'].count().pct_change().iloc[-1]*100
    pctChangeCas = mapData.groupby('Year')['casualities'].sum().pct_change().iloc[-1]*100
    col1.metric("Total Attacks",mapData.shape[0],f"{format(pctChangeAtt,'.3f')}%")
    col1.caption("Over past one year")
    col2.metric("Total Casualities",int(mapData['casualities'].sum()),f"{format(pctChangeCas,'.3f')}%")
    col2.caption("Over past one year")

## Impact Map
st.header('Locations of Attacks',divider=False)

st.map(mapData[['latitude','longitude']])

## Country Wise analysis
st.header("Country Wise Analysis")
chartTypeLog_toggle = st.toggle(label = "Log Analysis", value = True)

dft1 = mapData.groupby('Country')['casualities'].sum().rename('casualities_sum').reset_index()
dft2 = mapData.groupby('Country')['casualities'].count().rename('num_attacks').reset_index()
dft3 = mapData.groupby('Country')['Region'].agg(['unique']).apply(lambda x:x[0][0],axis=1).rename("Region").reset_index()
dft = pd.merge(left=dft1,right=dft2,on='Country')
dft = pd.merge(left=dft,right=dft3,on='Country')

fig = px.scatter(dft,x='casualities_sum',y='num_attacks',color='Region',hover_name="Country",log_x=chartTypeLog_toggle,log_y=chartTypeLog_toggle,size_max=60) 
fig.update_layout(title="Number of attacks v/s Casualities at a nation level")
fig.update_xaxes(title_text="Casualities")
fig.update_yaxes(title_text="Number of attacks")   

st.plotly_chart(fig)


## Frequency Cases
st.divider()
st.header(f'Changes in terrorism cases over time.')
# freq = st.select_slider('Select Frequency:',options = ['Week','Month','Quarter','Year'])
col1, col2 = st.columns(2)
with col1:  
    freq = st.segmented_control("Select Frequency",options=['Week','Month','Quarter','Year'],selection_mode="single",default='Week')
with col2:
    chartType_radio = st.radio(label="Chart Type:",options=['Line','Area'])

freqMap = {'Week':'W','Month':'M','Quarter':'Q','Year':'Y'}


if variable_radio=='Attacks':
    freqCount = mapData[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].count()
else:
    freqCount = mapData[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].sum()
fig = px.area(freqCount)
st.plotly_chart(fig)

## Weapon Details
st.divider()
st.subheader('Weapons and Casualties')
weaponsCasualities = mapData.groupby('Weapon_type')['casualities'].sum().sort_values(ascending=False)
fig = px.bar(weaponsCasualities)
# st.bar_chart(data = weaponsCasualities,color = '#bf3228')
st.plotly_chart(fig)

## Attack Details
st.divider()

col1, col2 = st.columns(2)
with col1:
    valCount1 = mapData['AttackType'].value_counts(sort=True).head(10)
    st.subheader("Attack Type")
    st.bar_chart(data=valCount1,horizontal = True, color = '#59ceeb')

with col2:
    valCount2 = mapData['Group'].value_counts(sort=True).head(10)
    st.subheader("Attacking Group")
    st.bar_chart(data=valCount2,horizontal = True, color = '#59ceeb')

st.divider()
st.header("Casualities v/s Target Types")
outlier_toggle = st.toggle(label = "Outlier Analysis", value = True)

if outlier_toggle:
    fig = px.box(data_frame=mapData,x='Target_type',y='casualities',log_y=True,points='suspectedoutliers')
    fig.update_yaxes(title_text="Casualities in Log")
else:
    fig = px.box(data_frame=mapData,x='Target_type',y='casualities',log_y=False,points=False)
    fig.update_yaxes(title_text="Casualities")
fig.update_xaxes(title_text="Target Type")
st.plotly_chart(fig)

# Image Showcase
# st.divider()
# st.header("Terrorism in Images")
# imgsPath = '/Users/asutoshdalei/Desktop/Work/GlobalTerrorism/terrorismImages/'
# imgs = os.listdir(imgsPath)[1:]
# idx = 0

# cont = st.empty()
# while idx < len(imgs):
#     print(imgs[idx])
#     cont.image(imgsPath+imgs[idx])
#     time.sleep(5)
#     idx+=1
#     if idx == len(imgs):
#         idx = 0



