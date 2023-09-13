import streamlit as st
import datetime
import csv
import os
import pandas as pd
import subprocess


# CSV file to store time logs
CSV_FILE = f"time_log_{datetime.datetime.now().strftime('%V_%Y')}.csv"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
VERSION = "0.1.2"
AUTHOR = "tzaeb"

st.set_page_config(layout="wide")
if 'input' not in st.session_state:
    st.session_state.input = ''

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
		return rows[-1][0], round(duration.seconds/3600,1)
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
	if get_current_task()[0] == None:
		col1.warning("No task currently running.")
	else:
		rows = read_csv(CSV_FILE)
		end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		rows[-1][2] = end_time
		with open(CSV_FILE, 'w', newline='') as file:
			writer = csv.writer(file)
			writer.writerows(rows)

def compute_time_difference(start, end):
	start_time = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
	end_time = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
	return (end_time - start_time).seconds

def report():
	total_times = {}
	total_sessions = {}
	total_duration = 0

	rows = read_csv(CSV_FILE)
	rows = rows[1:] # skip first row (header)
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
		data_list.append([task, f"{round(time, 1)}h", f"{round(percentage, 2)}%", f"{total_sessions[task]}", 'running <<' if get_current_task()[0]==task else 'paused'])
	
	# Convert list of lists to DataFrame for better table representation
	df = pd.DataFrame(data_list, columns=['Task', 'Time', 'Percentage', 'Sessions', 'Status'])
	col2.table(df)
	
	if total_times:
		chart_data = pd.DataFrame.from_dict(total_times, orient='index', columns=['Time (h)'])
		chart_data.index.name = 'Task'
		chart_info.bar_chart(chart_data)

def submit():
	input = st.session_state.widget.lower()
	st.session_state.widget = ''
	
	if input in ["", "re"]:
		pass
	elif input in ["pa", "end", "stop"]:
			stop_current_task()
	elif input.startswith("st") and input != "st":
		_, task  = [part.strip() for part in input.split(' ', 1)]
		start_task(task)
	else:
		col1.warning("command not supported")

def open_folder(folder_path):
	subprocess.run(f'explorer "{os.path.abspath(folder_path)}"')

def open_file(file_path):
	print("here")
	print(os.path.abspath(file_path))
	print("here")
	subprocess.run(f'code "{os.path.abspath(file_path)}"')

if not os.path.isfile(CSV_FILE):
	with open(CSV_FILE, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['task_name', 'start_time', 'end_time'])

st.title("Time Tracker")
st.markdown("**Supported commands**")
st.markdown("**st taskX** (start taskX), **pa** (pause current task), **re** (refresh task overview)")
st.divider()

col1, col2 = st.columns(2)
task_info = col1.empty()
chart_info = st.empty()
col1.text_input(" ", label_visibility="hidden", placeholder="Enter command", key='widget', on_change=submit)
col1.button("Open working directory", on_click=lambda: open_folder(os.getcwd()))
col1.button("Open current time log", on_click=lambda: open_file(CSV_FILE))

task, dur = get_current_task()
time_str = f"(since {dur} h)"
task_info.info(f'Current task: {"none" if task==None else task} {"" if task==None else time_str}')
report()

st.divider()
st.markdown(f'<p style="text-align: right;">Version: {VERSION}</p>', unsafe_allow_html=True)
