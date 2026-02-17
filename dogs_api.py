import streamlit as st
import pandas as pd
from copy import deepcopy
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from urllib.request import urlopen
import json

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    return df

df_raw = load_data('20200306_hundehalter.csv')
df = deepcopy(df_raw)

st.title('Dogs of Zurich')
#st.table(data = df)

st.write('This page presents some stats about the dogs that live in Zurich.')

# load in the json with geo locations
with open("stzh.adm_stadtkreise_a.json") as f:
    geojson = json.load(f)

# convert Stadtkreis to str as geojson contains strings
df['STADTKREIS'] = df['STADTKREIS'].astype(str)


# Figure 1. Breed popularity
#st.subheader('Breed popularity')
#st.write('A bar chart with with counts of dogs by breed - top 20')

rasse_df = df.groupby('RASSE1')['RASSE1'].agg('count').reset_index(name= "count")
rasse_df = rasse_df.sort_values(by="count", ascending=False).head(20)

highlight_values = ["Mischling klein", "Mischling gross"]

rasse_df["Breed category"] = rasse_df["RASSE1"].apply(
    lambda x: "Mixed breeds" if x in highlight_values else "Other breeds"
)
fig1 = px.bar(rasse_df, 
             x = rasse_df['RASSE1'], 
             y = rasse_df['count'],
             color = 'Breed category',
            labels={
        "RASSE1": "Dog Breed",   
        "count": "Dog count"   
    },
            color_discrete_map={
        "Mixed breeds": "lightblue",
        "Other breeds": "lightgray"
    }
            )
fig1.update_layout(
    title = 'Top 20 Dog Breeds in Zurich',
    xaxis_tickangle = 45
)
#st.plotly_chart(fig1)


# Figure 2. The Map
# st.subheader('Map')
# st.write('The map shows how many dogs per Zurich city district are registered.')

# total counts of dogs per neighbourhood
df_counts = df.groupby("STADTKREIS").size().reset_index(name="dog_count")
# Merge counts into GeoJSON
for feature in geojson["features"]:
    name = feature["properties"]["name"]
    counts = df_counts[df_counts["STADTKREIS"] == name]["dog_count"]
    feature["properties"]["dog_count"] = int(counts.tolist()[0]) if len(counts) > 0 else 0


# Create map with neighbourhoods coloured 
# from clear to dark by total number of dogs

fig2 = px.choropleth_map(
    df_counts,
    geojson=geojson,
    locations="STADTKREIS",
    featureidkey="properties.name",  
    color="dog_count",
    #animation_frame = 'RASSENTYP1',
    color_continuous_scale="blues",
    map_style="carto-positron",
    zoom=12,
    center={"lat": 47.37, "lon": 8.54},  # Zurich center
    #hover_data=["dog_count", "RASSENTYP1"],
    width = 800,
    height = 800,
    title= 'Count of dogs by neighbourhood'
)

#st.plotly_chart(fig2)

# Figure 3. Colors and breeds

# breed counts and top 30 most numerous breeds
df_breed_counts = df.groupby('RASSE1')['RASSE1'].count().reset_index(name = 'counts').sort_values(by = 'counts', ascending = False).head(30)
top30 = df_breed_counts["RASSE1"]
# breeds by colors
df_colors_breeds = df.groupby(["RASSE1", "HUNDEFARBE"])['RASSE1'].count().reset_index(name = 'count')

# isolating top 30 breeds
df_plot = df_colors_breeds[
    df_colors_breeds["RASSE1"].isin(top30)
]

#top colors
top_colors = (
    df["HUNDEFARBE"]
    .value_counts()
    .nlargest(10)
    .index
)

df_plot["HUNDEFARBE"] = df_plot["HUNDEFARBE"].where(
    df_plot["HUNDEFARBE"].isin(top_colors),
    "Other")

breeds = df_plot['RASSE1'].unique()

# color dictionary
from color_dict import dog_colors

# traces per breed, sorted by count descending
traces = []
for breed in breeds:
    df_breed = df_plot[df_plot['RASSE1'] == breed].copy()
    # Sort by count desc
    df_breed = df_breed.sort_values(by='count', ascending=False)
    
    traces.append(go.Bar(
        x=df_breed['HUNDEFARBE'],
        y=df_breed['count'],
        name=breed,
        marker_color=[dog_colors.get(c, "#808080") for c in df_breed['HUNDEFARBE']],
        visible=(breed == breeds[0])  # show only first breed initially
    ))

# figure
fig3 = go.Figure(data=traces)

# Dropdown buttons: toggle visibility
buttons = []
for i, breed in enumerate(breeds):
    visible = [False]*len(breeds)
    visible[i] = True
    buttons.append(dict(
        label=breed,
        method="update",
        args=[{"visible": visible},
              {"title": f"Number of Dogs: {breed}"}]
    ))

fig3.update_layout(
    title="Most popular colors of Top 30 Breeds",
    updatemenus=[dict(active=0, buttons=buttons, direction="down"),],
    plot_bgcolor = 'lightgrey'
)

#st.plotly_chart(fig3)

tab1, tab2, tab3 = st.tabs(["Dog Popularity", "Dog Map", "Breeds and Colors"])
with tab1:
    st.plotly_chart(fig1)
with tab2:
    st.plotly_chart(fig2)
with tab3:
    st.plotly_chart(fig3)