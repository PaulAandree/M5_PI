import pandas as pd
import streamlit as st
import seaborn as sns
import altair as alt

sns.set_theme(style="darkgrid")

# Assuming you have a DataFrame named 'df' with a 'date' and 'priority' column
df = pd.read_csv('call.csv')

# Convert the 'date' column to datetime
df['date'] = pd.to_datetime(df['date'])

# Add a new column for the week name
df['week_name'] = df['date'].dt.day_name()

# Add a sidebar section to display the filters
st.sidebar.title("Filter Options")

filter_by_month = st.sidebar.checkbox("Filter by Month")

# Get the minimum and maximum dates from the 'date' column
min_date = pd.to_datetime(df['date']).min().date()
max_date = pd.to_datetime(df['date']).max().date()

# Add a slider to select the date range
date_range = st.sidebar.slider(
    "Select the range of dates:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    format="MM/DD/YYYY"
)

# Convert the date_range values to datetime objects
# start_date = pd.to_datetime(date_range[0])
start_date = pd.to_datetime(date_range[0]).strftime("%m/%d/%Y")
end_date = pd.to_datetime(date_range[1]).strftime("%m/%d/%Y")

# Filter the DataFrame based on the selected date range
filtered_df = df[(pd.to_datetime(df['date']) >= start_date) & (pd.to_datetime(df['date']) <= end_date)]
filtered_df = filtered_df.drop(columns="Unnamed: 0") 

# Display the date range in the sidebar
st.sidebar.write(f"Selected Date Range: {start_date} to {end_date}")
############
df_without_NO_SERVER = df[df['server'] != 'NO_SERVER']

df_filter_no_server = st.sidebar.checkbox("DF without NO_SERVER")
#add a fomated text pryority={"2": "prioridad Alta", "1": "prioridad normal"}
filter_by_priority = st.sidebar.checkbox("Filter by Priority")
filter_by_type = st.sidebar.checkbox("Filter by Type")
filter_by_outcome = st.sidebar.checkbox("filter by Outcome")
filter_by_server = st.sidebar.checkbox("Filter by Server")

#################

if df_filter_no_server:
    filtered_df = filtered_df[filtered_df['server'] != 'NO_SERVER']

# Filter by month if the checkbox is activated
if filter_by_month:
    selected_month = st.sidebar.slider("Month", 1, 12, 1)
    filtered_df = filtered_df[pd.to_datetime(filtered_df['date']).dt.month == selected_month]
    
    # Check if the filtered DataFrame is empty
    if filtered_df.empty:
        st.write("The agent doesn't form part of the company anymore.")

# Filter by priority if the checkbox is activated
if filter_by_priority:
    selected_priority = st.sidebar.selectbox("Priority", df['priority'].unique())
    filtered_df = filtered_df[filtered_df['priority'] == selected_priority]

if filter_by_type:
    selected_type = st.sidebar.multiselect("Filter by Type", df['type'].unique())
    if selected_type:  # Check if any type is selected
        filtered_df = filtered_df[filtered_df['type'].isin(selected_type)]

if filter_by_outcome:
    selected_outcome = st.sidebar.selectbox("Outcome", df['outcome'].unique())
    filtered_df = filtered_df[filtered_df["outcome"]== selected_outcome]

if filter_by_server:
    selected_server = st.sidebar.selectbox("Server", df["server"].unique())
    filtered_df = filtered_df[filtered_df["server"] == selected_server]

    #i need the total agent's average time, which is the sum of q_time + ser_time for the 52 agents diviede by the row's number
    total_agents_time = df_without_NO_SERVER["q_time"].sum() + df_without_NO_SERVER["ser_time"].sum()
    total_agents_avg = round( ( (total_agents_time ) / len(df_without_NO_SERVER["server"])), 2 )
    total_agents_q_time_avg = round ((filtered_df["q_time"].sum() / len(filtered_df["server"])), 2)

    #calculates the productivity of each agent
    time = filtered_df["q_time"].sum() + filtered_df["ser_time"].sum()
    agents_avg = round( ( time / len(filtered_df["ser_time"]) ) ,2)
    productivity = round( ( agents_avg / total_agents_avg  ), 2 )*100

# to calculate the average times for the type of service:
df_types_t= filtered_df[["type", "vru_time", "q_time", "ser_time"]].copy()
df_types_t_avg  = df_types_t.groupby('type', as_index=False).mean().round(2)
df_melted = df_types_t_avg.melt(id_vars=['type'], var_name='Time', value_name='Time Value')

############
x1, x2, x3 = st.columns(3)

with x1:
    total_vru_time_avg = round ((df_without_NO_SERVER["vru_time"].sum() / len(df_without_NO_SERVER["server"])), 2)
    st.metric("Total vru time AVG: ", f"{total_vru_time_avg:.2f} sec.")

with x2:
    total_q_time_avg = round ((df_without_NO_SERVER["q_time"].sum() / len(df_without_NO_SERVER["server"])), 2)
    st.metric("Total Q time AVG: ", f"{total_q_time_avg:.2f} sec.")

with x3:
    total_ser_time_avg = round ((df_without_NO_SERVER["ser_time"].sum() / len(df_without_NO_SERVER["server"])), 2)
    st.metric("Total ser time AVG: ", f"{total_ser_time_avg:.2f} sec.")

c1, c2, c3 =st.columns(3)

with c1:
    if filter_by_server:
        st.metric("Agent's AVG Q time: ", f"{total_agents_q_time_avg:.2f} sec.")

with c2:
    target_time = st.text_input('Time for service level in seconds:', 90)
    st.write('The current service time is :', target_time + ' sg.')

with c3:
    if filter_by_server:
        st.metric("Agent's Name" , selected_server)

############
# if you want to see the filtered table in table format
filtered_table = st.checkbox("show me the filtered table.")

# Display the filtered DataFrame
if filtered_table:
    st.write(filtered_df)

nivel_servicio = round(((filtered_df[filtered_df["ser_time"] <= int(target_time) ]["ser_time"].count())/filtered_df.shape[0])*100, 2)
call_vol = filtered_df[filtered_df["outcome"] == "AGENT"]["outcome"].count()

#calculates the efficiency of each agent
efficiency = round(   (  int(target_time) / (filtered_df["ser_time"].sum() / filtered_df["ser_time"].count())  )  * 100, 2)

# Calculate the number of calls for each day along with the week name
calls_per_day = filtered_df.groupby([ filtered_df['date'].dt.day_name()]).size().reset_index(name='number_of_calls')
calls_per_day = calls_per_day.sort_values("number_of_calls", ascending=True)

#### this section will discard the 0's, both in the ser_start_hours and hour_band because has as an outcome: HANG
df_no_zero = filtered_df[filtered_df["hour_band"] != 0]

# this line will ignore all customoer_id's equal to 0
df_without_zero_clients = filtered_df[filtered_df["customer_id"] != 0]

# function to the repetitive task of getting the column's value counts into a table
def get_value_counts(dataframe, column_name):
    value_counts_series = dataframe[column_name].value_counts().reset_index()
    value_counts_series.columns = [column_name, 'count']
    return value_counts_series

# Calculate value counts of 'hour_band', 'ser_start_hours' and "type"
value_counts_band = get_value_counts(df_no_zero, 'hour_band')
#value_counts_band = value_counts_band.sort_values("count", ascending=True)
value_counts_hours = get_value_counts(df_no_zero, 'ser_start_hours')
value_counts_type = get_value_counts(filtered_df, 'type')
value_count_client = get_value_counts(df_without_zero_clients, "customer_id")

# Rank the customers by count in descending order
value_count_client['rank'] = value_count_client['count'].rank(ascending=False)

# Filter to keep only the top 7 rows (top 7 customers)
top_7_customers = value_count_client[value_count_client['rank'] <= 7]

# Calculate the maximum number of calls and the corresponding day
max_calls = calls_per_day['number_of_calls'].max()
max_calls_day = calls_per_day.loc[calls_per_day['number_of_calls'].idxmax(), 'date']

# Create the bar chart using Altair
chart_customers = alt.Chart(top_7_customers).mark_bar().encode(
    x= 'count:Q',
    y=alt.Y('customer_id:O', axis=alt.Axis(title='Customers')),
).properties(
    width=400,
    height=300,
    title='Top 7 Customer Counts'
)

# Create the Altair chart
chart_types_t_avg = alt.Chart(df_melted).mark_bar().encode(
    x='Time Value',
    y='type',
    color=alt.Color('Time', legend =None),
    tooltip=['type', 'Time', 'Time Value']
).properties(
    width=400,
    height=300
)




# Create the bar chart using Altair
chart_types = alt.Chart(value_counts_type).mark_bar().encode(
    x='count:Q' ,
    y=alt.Y('type:O', axis=alt.Axis(title='Call Types')),
).properties(
    width=400,
    height=300,
    title='Call Type Counts'
)

# Create the bar chart using Altair
chart_hours = alt.Chart(value_counts_hours).mark_bar().encode(
    x='count:Q' ,
    y=alt.Y('ser_start_hours:O', axis=alt.Axis(title='Hours')),
).properties(
    width=400,
    height=650,
    title='Hour call Counts'
)

# Create a bar plot to display the calls per day
chart = alt.Chart(calls_per_day).mark_bar().encode(
    x=alt.X('number_of_calls:Q', axis=alt.Axis(title='Number of Calls')),
    y=alt.Y('date:N', sort='x')
).properties(
    width=500,
    height=300,
    title='Number of Calls per Day'
)

# Create the bar chart using Altair with a tooltip for the hour range
chart_band_hours = alt.Chart(value_counts_band).mark_bar().encode(
    x=alt.X('count:Q', axis=alt.Axis(title='Count')),
    y=alt.Y('hour_band:O', axis=alt.Axis(title='Hour Band')),

).transform_calculate(
    hour_range='datum.hour_band == 1 ? "1 am to 7 am" : datum.hour_band == 2 ? "8 am to 3 pm" : "4 pm to 11 pm"'
).properties(
    width=250,
    height=300,
    title='Hour Band Counts'
).encode(
    tooltip=[
        alt.Tooltip('hour_range:N', title='Hour Range'),
        alt.Tooltip('count:Q', title='Count', format='.0f'),
    ]
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label = "Service Level" , value="{:.2f} %".format(nivel_servicio))

with col2:
    st.metric(label = "Calls Answered", value= "{:,.0f}".format(call_vol))

with col3:
    st.metric("Max Number of Calls", value= "{:,.0f}".format(max_calls))

with col4:
    st.metric("Day with Max Calls", max_calls_day)

# Display the table
# st.write(calls_per_day)

# Display the bar plot
st.altair_chart(chart, use_container_width=True)

col_1, col_2 = st.columns(2)

with col_1:
    st.altair_chart(chart_hours, use_container_width=True)

with col_2:
    st.altair_chart(chart_band_hours, use_container_width=True)

with col_2:
    st.altair_chart(chart_types, use_container_width=True )


s1, s2 = st.columns(2)

with s1:
# Display the bar plot
    st.altair_chart(chart_customers, use_container_width=True)
with s2:
    st.altair_chart(chart_types_t_avg, use_container_width=True)

b1, b2, b3 = st.columns(3)

with b1:
    st.metric(label = "Agent's efficiency", value="{:.2f} %".format(efficiency) )

with b2:
    if filter_by_server:
        st.metric(label = "Agent's productivity", value="{:.2f} %".format(productivity) )
    
