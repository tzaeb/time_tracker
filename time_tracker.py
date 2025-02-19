import streamlit as st
import datetime
import csv
import os
import pandas as pd
import subprocess
import altair as alt

# CSV file to store time logs
CSV_FILE = f"time_log_{datetime.datetime.now().strftime('%V_%Y')}.csv"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
VERSION = "0.2.1"

st.set_page_config(layout="wide")
if 'widget' not in st.session_state:
    st.session_state.widget = ''

def read_csv(file_path):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            return list(csv.reader(file))
    else:
        return None

def get_current_task():
    rows = read_csv(CSV_FILE)
    if rows and not rows[-1][2]:
        start_time = datetime.datetime.strptime(rows[-1][1], DATE_FORMAT)
        duration = datetime.datetime.now() - start_time
        return rows[-1][0], round(duration.total_seconds()/3600, 1)
    else:
        return None, 0

def start_task(task_name):
    if not task_name.strip():
        col1.warning("Task name cannot be empty.")
        return
    if task := get_current_task()[0]:
        col1.warning(f"'{task}' stopped, '{task_name}' started")
        stop_current_task()
    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        start_time = datetime.datetime.now().strftime(DATE_FORMAT)
        writer.writerow([task_name, start_time, ""])

def stop_current_task():
    if get_current_task()[0] is None:
        col1.warning("No task currently running.")
    else:
        rows = read_csv(CSV_FILE)
        end_time = datetime.datetime.now().strftime(DATE_FORMAT)
        rows[-1][2] = end_time
        with open(CSV_FILE, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

def compute_time_difference(start, end):
    start_time = datetime.datetime.strptime(start, DATE_FORMAT)
    end_time = datetime.datetime.strptime(end, DATE_FORMAT)
    return (end_time - start_time).total_seconds()

def report():
    total_times = {}
    total_sessions = {}
    total_duration = 0

    rows = read_csv(CSV_FILE)
    rows = rows[1:]  # skip first row (header)
    for row in rows:
        duration = compute_time_difference(row[1], row[2] if row[2] else datetime.datetime.now().strftime(DATE_FORMAT))
        total_duration += duration/3600
        if row[0] in total_times:
            total_times[row[0]] += duration/3600
            total_sessions[row[0]] += 1
        else:
            total_times[row[0]] = duration/3600
            total_sessions[row[0]] = 1

    col2.markdown(f"**Time Report (total: {round(total_duration,1)} h**)")

    data_list = []
    for task, time in total_times.items():
        percentage = (time / total_duration) * 100 if total_duration else 0
        data_list.append([task, f"{round(time, 1)}h", f"{round(percentage, 2)}%", f"{total_sessions[task]}",
                          'running <<' if get_current_task()[0] == task else 'paused'])
    
    # Convert list of lists to DataFrame for better table representation
    df = pd.DataFrame(data_list, columns=['Task', 'Time', 'Percentage', 'Sessions', 'Status'])
    col2.table(df)
    
    if total_times:
        # Prepare data for enhanced bar chart
        chart_data = pd.DataFrame.from_dict(total_times, orient='index', columns=['Time (h)'])
        chart_data.index.name = 'Task'
        chart_data = chart_data.reset_index()
        
        # Enhanced bar chart with improved UI and no border/stroke
        chart = alt.Chart(chart_data).mark_bar(
            size=25,  # Slightly thinner bars for better spacing
            cornerRadius=8,  # Unified rounded corners
            stroke=None  # Remove stroke from bars
        ).encode(
            x=alt.X('Time (h):Q', 
                   title='Hours Spent',
                   axis=alt.Axis(grid=True, gridOpacity=0.2)),
            y=alt.Y('Task:N', 
                   sort='-x',
                   title='Tasks',
                   axis=alt.Axis(labels=True, titleAngle=0, titleAlign='right')),
            color=alt.condition(
                alt.datum.Task == get_current_task()[0],
                alt.value('#dca11d'),  # Highlight current task
                alt.value('#4a86e8')   # Other tasks
            ),
            tooltip=[
                alt.Tooltip('Task:N', title='Task'),
                alt.Tooltip('Time (h):Q', title='Hours', format='.1f')
            ]
        ).properties(
            width=600,
            height=alt.Step(40),  # Adjusted height per bar
            title=alt.TitleParams(
                text='Task Time Distribution',
                anchor='middle',
                fontSize=16,
                offset=10
            )
        ).configure(
            view=alt.ViewConfig(strokeWidth=0),  # Remove outer border
            mark=alt.MarkConfig(
                opacity=0.9  # Removed stroke-related properties
            ),
            axis=alt.AxisConfig(
                labelFontSize=12,
                titleFontSize=14
            )
        )

        chart_info.altair_chart(chart, use_container_width=True)

def submit():
    user_input = st.session_state.widget.lower()
    st.session_state.widget = ''
    
    if user_input in ["", "re"]:
        pass
    elif user_input in ["pa", "end", "stop"]:
        stop_current_task()
    elif user_input.startswith("st") and user_input != "st":
        try:
            _, task = [part.strip() for part in user_input.split(' ', 1)]
            start_task(task)
        except ValueError:
            col1.warning("Invalid command format. Use: st <task_name>")
    else:
        col1.warning("command not supported")

def open_folder(folder_path):
    subprocess.run(f'explorer "{os.path.abspath(folder_path)}"')

def open_file(file_path):
    subprocess.run(f'code "{os.path.abspath(file_path)}"')

if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['task_name', 'start_time', 'end_time'])

st.title("Time Tracker")

col1, col2 = st.columns(2)
cmds = "Commands: **st taskXYZ** (start taskX) / **pa** (pause task) / **re** (refresh overview)"
col1.text_input(cmds, label_visibility="visible", placeholder="Enter command", key='widget', on_change=submit)
task_info = col1.empty()
chart_info = st.empty()
col11, col22 = col1.columns(2)
col11.button("Open working directory", on_click=lambda: open_folder(os.getcwd()))
col22.button("Open time log", on_click=lambda: open_file(CSV_FILE))

task, dur = get_current_task()
time_str = f"(since {dur} h)"
task_info.info(f'Current task: {"none" if task is None else task} {"" if task is None else time_str}')
report()

st.markdown(f'<p style="text-align: right;">Version: {VERSION}</p>', unsafe_allow_html=True)
