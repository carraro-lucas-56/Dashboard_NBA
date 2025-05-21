import streamlit as st
import pandas as pd
import plotly.express as px

df = pd.read_csv("./database_24_25.csv")
df_ps = pd.read_csv("./database_23_24.csv")

#
# helpful funcitons
#

@st.cache_data
def get_players():
    return df['Player'].unique()

@st.cache_data
def get_teams():
    return df['Tm'].unique()

@st.cache_data
def get_player_data(player_name,df):
    df_player = (df[df['Player'] == player_name]
                  .drop(['Player'],axis=1)
                  .set_index('Data'))
    df_player.index = pd.to_datetime(df_player.index).date
    return df_player

@st.cache_data
def get_team_data(team_name,df):
    df_team = (df[df['Tm'] == team_name]
                  .drop(['Tm'],axis=1)
                  .set_index('Data'))
    df_team.index = pd.to_datetime(df_team.index).date
    return df_team

#
# Filters
#

st.sidebar.title('Filters')

selected_player = st.sidebar.selectbox('Choose your favorite player \U0001F609.',get_players())

selected_stat = st.sidebar.selectbox(
            'Choose the player stat you wanna analyze deeply',
            df.drop(['Tm','MP','Res','Opp','Player'],axis=1).columns,
            key=1)

selected_team = st.sidebar.selectbox('Choose your favorite team \U0001F609.',get_teams())

#
# Tables
#

#
# stats for the 2024-25 season
#

df_player = get_player_data(selected_player,df)
df_team = get_team_data(selected_team,df)
df_game_results = df_team[df_team.index.duplicated(keep='first')]['Res']

points_per_game = df_team.groupby(level=0)[['PTS','Opp']].sum()

points_suffered = df[df['Opp'] == selected_team][['Data','PTS']].groupby('Data').sum()
points_suffered.index = pd.to_datetime(points_suffered.index).date

df_game_score = pd.merge(left=points_per_game,right=points_suffered,left_index=True,right_index=True)
df_game_score.columns = ['Pts made','Opponent','Pts suffered']
df_game_score['Point diff'] = df_game_score['Pts made'] - df_game_score['Pts suffered']
df_game_score['Opponent'] = df_game_score['Opponent'].map(lambda str: str[:3])

#
# stats for the 2023-24 season (past season)
#

df_player_ps = get_player_data(selected_player,df_ps)

if(df_player_ps.empty):
    df_player_ps=df_player

df_team_ps = get_team_data(selected_team,df_ps)
df_game_results_ps = df_team_ps[df_team_ps.index.duplicated(keep='first')]['Res']

points_per_game_ps = df_team_ps.groupby(level=0)['PTS'].sum()
points_suffered_ps = df_ps[df_ps['Opp'] == selected_team][['Data','PTS']].groupby('Data').sum()
points_suffered_ps.index = pd.to_datetime(points_suffered_ps.index).date

#
# Graphs
#

fig_season_means = px.bar(df_player.drop(columns=['Tm','Opp','Res'])
                                   .agg('mean')
                                   .round(2),
                          text_auto = True,
                          labels={"variable":"values"})
fig_season_means.update_layout(xaxis_title='Statistis',
                               yaxis_title='Averages',
                               title=dict(text=f'{selected_player}\u0027s season avarage for all categories',
                                          font=dict(size=18)
                               ))
fig_season_means.update_traces(hovertemplate="<b>%{x}</b><br>Mean: %{y}<extra></extra>")

fig_stat_per_minute = px.scatter(df_player,
                                 x='MP',
                                 y=selected_stat,
                                 color_discrete_sequence=['crimson'])
fig_stat_per_minute.update_layout(xaxis_title='<b>Minutes played</b>',
                                  yaxis_title=f'<b>{selected_stat}</b>',
                                  title=dict(text=f'<b>{selected_stat} vs Minutes played</b>',
                                             x=0.2,
                                             xanchor='left',
                                             font=dict(size= 18)
                                 ))

fig_stat_per_game = px.line(df_player[selected_stat],
                            markers=True)
fig_stat_per_game.update_traces(line_color='red',
                                marker=dict(color='white', 
                                            size=5
                                ))
fig_stat_per_game.update_layout(xaxis_title='<b>Games</b>',
                                yaxis_title=f'<b>{selected_stat}</b>',
                                title=dict(text=f'<b>{selected_stat} history per game</b>',
                                           x=0.12,
                                           xanchor='left',
                                           font=dict(size=18)
                                ))

df_game_score["Bar color"] = df_game_score["Point diff"].apply(lambda x: "Win" if x > 0 else "Loss")

fig_game_score = px.bar(df_game_score,
                        x=df_game_score.index,
                        y='Point diff',
                        color='Bar color',
                        color_discrete_map={"Win": "#32CD32", "Loss": "#FF6347"},
                        labels={"Bar color": "Game Outcome"},
                        hover_data=['Opponent'])
fig_game_score.update_layout(xaxis_title="Games",
                             yaxis_title="Point difference",
                             title=dict(text=f'<b>{selected_team}\u0027s game history</b>',
                                        x=0.12,
                                        xanchor='left',
                                        font=dict(size=18)
                            ))


#
# streamlit's layout
#

tab1, tab2 = st.tabs(['Player statistics','Team statistics'])

with tab1:
    st.title(f"Stats for {selected_player} \U0001F3C0")
    st.metric('Games played: ',df_player.shape[0],delta=df_player.shape[0]-df_player_ps.shape[0])

    st.plotly_chart(fig_season_means)

    col1, col2 = st.columns(2)

    with col1:
        average = df_player[selected_stat].mean().round(2)
        average_ps = df_player_ps[selected_stat].mean().round(2) # average from the past season
        st.metric(f'{selected_stat} avarage: ',average
                                              ,delta=round(average-average_ps,2)
                                              ,help="Comparison with last season")
        st.plotly_chart(fig_stat_per_game)
    with col2:
        season_high = df_player[selected_stat].max()
        season_high_ps = df_player_ps[selected_stat].max()
        st.metric(f'{selected_stat} season high: ',season_high
                                                  ,int(season_high-season_high_ps)
                                                  ,help="Comparison with last season")
        st.plotly_chart(fig_stat_per_minute)

with  tab2:
    st.title(f"Stats for {selected_team} \U0001F3C0")

    col1, col2, col3 = st.columns(3)

    with col1:
        win_rate = df_game_results.value_counts().loc['W']/df_game_results.shape[0]*100
        win_rate_ps = df_game_results_ps.value_counts().loc['W']/df_game_results_ps.shape[0]*100
        st.metric(f'Winrate:',f'{round(win_rate,1)}%'
                             ,delta=round(win_rate-win_rate_ps,1)
                             ,help="Comparison with last season")
    with col2:
        ppg_average = points_per_game['PTS'].mean()
        ppg_average_ps = points_per_game_ps.mean()
        st.metric(f'Points made per game:',round(ppg_average,1)
                                          ,delta=round(ppg_average-ppg_average_ps,1)
                                          ,help="Comparison with last season")
    with col3:
        pspg = points_suffered.mean().loc['PTS'] # pts suffered per game
        pspg_ps = points_suffered_ps.mean().loc['PTS'] 
        st.metric(f'Points suffered per game:',round(pspg,1)
                                              ,delta=round(pspg-pspg_ps,1)
                                              ,delta_color='inverse'
                                              ,help="Comparison with last season")

    st.plotly_chart(fig_game_score)