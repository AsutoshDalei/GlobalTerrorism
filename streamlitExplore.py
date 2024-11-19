import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")



def dateFnx(row):
    date = str(row['Month'])+':'+str(row['Day'])+':'+str(row['Year'])
    return pd.to_datetime(date,format='%m:%d:%Y')



@st.cache_data
def fetch_and_clean_data(path,nrows = 10000):
    data = pd.read_csv(path,encoding= 'ISO-8859-1',nrows=nrows)
    data.rename(columns={'iyear':'Year','imonth':'Month','iday':'Day','country_txt':'Country','region_txt':'Region','attacktype1_txt':'AttackType','target1':'Target','nkill':'Killed','nwound':'Wounded','summary':'Summary','gname':'Group','targtype1_txt':'Target_type','weaptype1_txt':'Weapon_type','motive':'Motive'},inplace=True)

    data=data[['Year','Month','Day','Country','Region','city','latitude','longitude','AttackType','Killed','Wounded','Target','Summary','Group','Target_type','Weapon_type','Motive']]
    data['casualities']=data['Killed']+data['Wounded']

    data = data[(data.Month!=0) & (data.Day!=0)]
    data['date'] = data.apply(dateFnx,axis=1)
    return data

path = "/Users/asutoshdalei/Desktop/Work/GlobalTerrorism/globalterrorismdb.csv"
data = fetch_and_clean_data(path)

countryWise = data.groupby('Country')['casualities'].sum()
countryList = countryWise[countryWise>5].index.tolist()


# Streamlit section
st.title("Global Terrorism Impact")
## Sidebar
with st.sidebar:
    st.header("Global Terrorism Analysis")
    st.subheader('Select Analysis Options')

    mapFlag = st.toggle(label = "Region/Country Toggle", value = True)
    variable_radio = st.radio(label="Analysis Measure:",options=['Cases','Casualities'])
    
    if mapFlag == True:
        mapFlagCol = 'Region'
        mapSelection = st.multiselect(label='Select Region',options = data.Region.unique().tolist()+['Global'],default='Global')
        if 'Global' in mapSelection:
            mapSelection = data.Region.unique().tolist()
    else:
        mapFlagCol = 'Country'
        mapSelection = st.multiselect(label='Select Country',options = data.Country.unique().tolist()+['Global'],default='Global')
        if 'Global' in mapSelection:
            mapSelection = data.Country.unique().tolist()


## Impact Map
st.header('Locations of Attacks',divider=True)
mapData = data[data.latitude.notna() & data.longitude.notna() & data[mapFlagCol].isin(mapSelection)]
st.map(mapData[['latitude','longitude']])



## Frequency Cases
st.divider()
# freq = st.select_slider('Select Frequency:',options = ['Week','Month','Quarter','Year'])

freq = st.segmented_control("Select Frequency",options=['Week','Month','Quarter','Year'],selection_mode="single",default='Week')
freqMap = {'Week':'W','Month':'M','Quarter':'Q','Year':'Y'}

st.header(f'Rise of attacks over a {freq.lower()} frequency.',divider=True)
if variable_radio=='Cases':
    # freqCount = data[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].count()
    freqCount = mapData[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].count()
else:
    # freqCount = data[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].sum()
    freqCount = mapData[['casualities','date']].set_index('date').resample(freqMap[freq])['casualities'].sum()
st.line_chart(data=freqCount)

## Attack Details
st.divider()

col1, col2 = st.columns(2)
with col1:
    valCount1 = mapData['AttackType'].value_counts()
    st.subheader("Attack Type")
    st.bar_chart(data=valCount1,color=plt.cm.get_cmap('cool',len(valCount1)))


