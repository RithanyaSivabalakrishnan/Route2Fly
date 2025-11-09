# Route2Fly
Route2Fly is a fun and interactive Python desktop app for visualizing and exploring optimized domestic flight routes across India. Built with Tkinter, NetworkX, and Matplotlib, it helps you find the best connections, see alternative layovers, and understand the Indian air network in a super user-friendly way!

# ✈️ Features
•	Visualize Indian domestic flight networks — easy interactive map & route graphs.

•	Smartest route selection — always finds the shortest (cheapest/quickest) path using Dijkstra’s algorithm.

•	Top 3 alternate routes — gives you practical and different options using a custom DFS search.

•	Side-by-side details — see all available flights for a chosen date, with clear and friendly tables.

•	Airport legend at a glance — always know what codes stand for which cities.

•	Date picker for easy search — just tap the calendar to pick your journey date, no need to remember date formats.

# 🚀 How it Works
1.	Select source and destination cities from the dropdowns.
2.	Choose your journey date with the built-in calendar picker.
3.	Set your preference: optimize for Duration, Price, or Both.
4.	Click "Optimize" – the app will:

•	Build a flight network from real CSV data.

•	Show you a map with all relevant paths and layovers.

•	List the best and alternate routes, so you can compare them.

•	Give you the airport code legend for every node in the graph.

# 🛠️ Tech Stack
•	Python 3.x

•	Tkinter (for the GUI)

•	NetworkX (for graph magic)

•	Matplotlib (for visualization)

•	Pandas (for flight data wrangling)

•	tkcalendar (for journey date picking)

•	heapq (for Dijkstra’s algorithm, under the hood)

# Data Source
This project uses the following Kaggle dataset:

Flight Price Dataset - India 2019

Author: Ankush Sonar

Kaggle. https://www.kaggle.com/datasets/ankushsonar/flight-price-dataset-india-2019
