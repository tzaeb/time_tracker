import streamlit as st
import datetime
import csv
import os
import pandas as pd


# CSV file to store time logs
CSV_FILE = f"time_log_{datetime.datetime.now().strftime('%V_%Y')}.csv"

def running_task():
	if os.path.isfile(CSV_FILE):
		with open(CSV_FILE, 'r') as file:
			rows = list(csv.reader(file))
			if rows and not rows[-1][2]:
				start_time = datetime.datetime.strptime(rows[-1][1], "%Y-%m-%d %H:%M:%S")
				duration = datetime.datetime.now() - start_time
				return rows[-1][0], round(duration.seconds/3600,1)
			else:
				return None, 0
	else:
		return None, 0

def get_all_tasks():
	if os.path.isfile(CSV_FILE):
		with open(CSV_FILE, 'r') as file:
			rows = list(csv.reader(file))
			tasks = [row[0] for row in rows]
			return list(set(tasks))
	else:
		return []

def start_task(task_name):
	with open(CSV_FILE, 'r') as file:
		rows = list(csv.reader(file))
		if rows==[] or rows[-1][2]:
			with open(CSV_FILE, "a", newline="") as file:
				writer = csv.writer(file)
				start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				writer.writerow([task_name, start_time, ""])
				st.write(f"Started working on {task_name} at {start_time}.")
		else:
			col1.warning("Task not stopped.")

def stop_task():
	with open(CSV_FILE, 'r') as file:
		rows = list(csv.reader(file))

	if not rows[-1][2]:
		end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		rows[-1][2] = end_time

		with open(CSV_FILE, 'w', newline='') as file:
			writer = csv.writer(file)
			writer.writerows(rows)

		st.write(f"Stopped working on {rows[-1][0]} at {end_time}.")
	else:
		st.warning("No task currently running.")

def compute_time_difference(start, end):
	start_time = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
	end_time = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
	return (end_time - start_time).seconds

def report():
	total_times = {}
	total_duration = 0

	with open(CSV_FILE, 'r') as file:
		reader = csv.reader(file)
		next(reader)  # skip the first row
		for row in reader:
			#if row[2]:  # only consider rows where tasks have stopped
			duration = compute_time_difference(row[1], row[2] if row[2] else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
			total_duration += duration/3600
			if row[0] in total_times:
				total_times[row[0]] += duration/3600
			else:
				total_times[row[0]] = duration/3600


	col2.markdown(f"**Time Report (total: {round(total_duration,1)} h**)")
	data_list = []
	for task, time in total_times.items():
		percentage = (time / total_duration) * 100 if total_duration else 0
		data_list.append([task, str(round(time, 1))+"h", str(round(percentage, 2))+ "%", 'running' if running_task()[0]==task else 'paused'])
	# Convert list of lists to DataFrame for better table representation
	df = pd.DataFrame(data_list, columns=['Task', 'Time', 'Percentage', 'Status'])

	col2.table(df)
	chart_data = pd.DataFrame.from_dict(total_times, orient='index', columns=['Time (h)'])
	chart_data.index.name = 'Task'
	chart_info.bar_chart(chart_data)


if not os.path.isfile(CSV_FILE):
	with open(CSV_FILE, 'w', newline='') as file:
		writer = csv.writer(file)
		writer.writerow(['task_name', 'start_time', 'end_time'])

st.title("Time Tracker (v0.1.0)")
st.markdown("**Supported commands**")
st.markdown("**st taskX** (starts taskX), **br** (ends last task), **rep** (shows task overview)")
st.divider()

col1, col2 = st.columns(2)
task_info = col1.empty()
chart_info = st.empty()
input = col1.text_input("", label_visibility="hidden", placeholder="Enter command").lower()

if input in ["", "rep"]:
	pass
elif input in ["br", "end", "stop"]:
		stop_task()
elif input.startswith("st"):
	cmd, task  = [part.strip() for part in input.split(' ', 1)]
	start_task(task)
else:
	col1.warning("command not supported")

task, dur = running_task()
time_str = f"(since {dur} h)"
task_info.info(f'Current task: {"none" if task==None else task} {"" if task==None else time_str}')
report()
