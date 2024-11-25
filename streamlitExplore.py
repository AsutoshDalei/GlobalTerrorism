import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
import time
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
    return data

path = "/Users/asutoshdalei/Desktop/Work/GlobalTerrorism/globalterrorismdb.csv"
data = fetch_and_clean_data(path,nrows= -1)

countryWise = data.groupby('Country')['casualities'].sum()
countryList = countryWise[countryWise>5].index.tolist()

# Streamlit section
st.title("Global Terrorism Impact")
## Sidebar
with st.sidebar:
    # imgPath = 'https://www.google.com/url?sa=i&url=https%3A%2F%2Fstock.adobe.com%2Fsearch%3Fk%3Dglobal%2Bterrorism&psig=AOvVaw1at4COBS15aJmBDExfObUY&ust=1732377795838000&source=images&cd=vfe&opi=89978449&ved=0CBQQjRxqFwoTCNj_1ayo8IkDFQAAAAAdAAAAABAE'
    # st.image(imgPath)
    st.header("Global Terrorism Analysis")
    st.subheader('Select Analysis Options')

    mapFlag = st.toggle(label = "Region/Country Toggle", value = True)
    variable_radio = st.radio(label="Analysis Measure:",options=['Cases','Casualities'])
    
    if mapFlag == True:
        mapFlagCol = 'Region'
        mapSelection = st.multiselect(label='Select Region',options = data.Region.unique().tolist()+['Global'],default='Global')
        if ('Global' in mapSelection) or (mapSelection==[]):
            mapSelection = data.Region.unique().tolist()
    else:
        mapFlagCol = 'Country'
        mapSelection = st.multiselect(label='Select Country',options = data.Country.unique().tolist()+['Global'],default='Global')
        if ('Global' in mapSelection) or (mapSelection==[]):
            mapSelection = data.Country.unique().tolist()

minTime,maxTime = data[data.latitude.notna() & data.longitude.notna()]['date'].agg(['min','max'])
dateRangeOptions = pd.date_range(minTime,maxTime,freq = 'W').strftime('%Y-%m-%d').tolist()
start_time,end_time = st.select_slider(label='Date Range',options=dateRangeOptions,value=(dateRangeOptions[0],dateRangeOptions[-1]))

## Impact Map
st.header('Locations of Attacks',divider=False)

mapData = data[data.latitude.notna() & data.longitude.notna() & data[mapFlagCol].isin(mapSelection) & (data['date']>=start_time) & (data['date']<=end_time)]
# clicked = st.toggle(label = "Timeline", value = False)

# if clicked:
#     latDt = mapData.groupby(['Year','Month'])['latitude'].apply(list)
#     lonDt = mapData.groupby(['Year','Month'])['longitude'].apply(list)
#     mapPlot = st.map(pd.DataFrame({'LAT':latDt.iloc[0],'LON':lonDt.iloc[0]}),zoom=15)
#     for ydt in latDt.index.to_list()[1:]:
#         tempDf = pd.DataFrame({'LAT':latDt[ydt],'LON':lonDt[ydt]})
#         mapPlot.add_rows(tempDf)
#         time.sleep(0.5)
# else:
#     st.map(mapData[['latitude','longitude']])

st.map(mapData[['latitude','longitude']])



## Country Wise analysis
st.header("Country Wise Analysis")
chartTypeLog_toggle = st.toggle(label = "Log Analysis", value = True)

dft1 = mapData.groupby('Country')['casualities'].sum().rename('casualities_sum').reset_index()
dft2 = mapData.groupby('Country')['casualities'].count().rename('num_attacks').reset_index()
dft3 = mapData.groupby('Country')['Region'].agg(['unique']).apply(lambda x:x[0][0],axis=1).rename("Region").reset_index()
dft = pd.merge(left=dft1,right=dft2,on='Country')
dft = pd.merge(left=dft,right=dft3,on='Country')

if chartTypeLog_toggle:
    fig = px.scatter(dft,x='casualities_sum',y='num_attacks',color='Region',hover_name="Country",log_x=True,log_y=True,size_max=60) 
else:
    fig = px.scatter(dft,x='casualities_sum',y='num_attacks',color='Region',hover_name="Country",log_x=False,log_y=False,size_max=60)
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


if variable_radio=='Cases':
    # freqCount = data[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].count()
    freqCount = mapData[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].count()
else:
    # freqCount = data[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].sum()
    freqCount = mapData[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].sum()

if chartType_radio == 'Line':
    st.line_chart(data=freqCount,color='#bf3228')
else:
    st.area_chart(data=freqCount,color='#bf3228')

## Weapon Details
st.divider()
st.subheader('Weapons and Casualties')
weaponsCasualities = mapData.groupby('Weapon_type')['casualities'].sum().sort_values()
st.bar_chart(data = weaponsCasualities,color = '#bf3228')

## Attack Details
st.divider()

col1, col2 = st.columns(2)
with col1:
    valCount1 = mapData['AttackType'].value_counts(sort=True).head(10)
    st.subheader("Attack Type")
    st.bar_chart(data=valCount1,horizontal = True, color = '#ad331a')

with col2:
    valCount2 = mapData['Group'].value_counts(sort=True).head(10)
    st.subheader("Attacking Group")
    st.bar_chart(data=valCount2,horizontal = True, color = '#ada11a')


