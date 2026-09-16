import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

DB_NAME = "support_queue.db"

# -----------------------------
# Database
# -----------------------------
def get_connection():
	return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
	conn = get_connection()

	conn.execute("""
		CREATE TABLE IF NOT EXISTS tickets (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			customer TEXT NOT NULL,
			title TEXT NOT NULL,
			description TEXT,
			priority TEXT NOT NULL,
			response_due TEXT NOT NULL,
			assignee TEXT,
			status TEXT NOT NULL DEFAULT 'Open',
			created_at TEXT NOT NULL
		)
	""")

	conn.commit()

	# Add demo data only when database is empty
	count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]

	if count == 0:
		now = datetime.now()

		demo_tickets = [
			(
				"Priya Sharma",
				"Laptop won't boot before client demo",
				"Laptop is not starting and client demo is scheduled soon.",
				"Urgent",
				(now - timedelta(minutes=20)).isoformat(),
				"Arjun",
				"Open",
				(now - timedelta(hours=2)).isoformat(),
			),
			(
				"Rahul Mehta",
				"VPN connection failing",
				"Unable to connect to company VPN.",
				"Urgent",
				(now + timedelta(minutes=30)).isoformat(),
				"Priya",
				"Open",
				(now - timedelta(hours=1)).isoformat(),
			),
			(
				"Ankit Verma",
				"Can I get a bigger monitor?",
				"Requesting a larger monitor for development work.",
				"Normal",
				(now + timedelta(hours=5)).isoformat(),
				None,
				"Open",
				(now - timedelta(minutes=40)).isoformat(),
			),
			(
				"Neha Singh",
				"Email password reset",
				"Customer needs help resetting email password.",
				"Normal",
				(now + timedelta(hours=2)).isoformat(),
				"Arjun",
				"Open",
				(now - timedelta(minutes=20)).isoformat(),
			),
		]

		conn.executemany("""
			INSERT INTO tickets
			(customer, title, description, priority, response_due,
			 assignee, status, created_at)
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)
		""", demo_tickets)

		conn.commit()

	conn.close()

def load_tickets():
	conn = get_connection()

	df = pd.read_sql_query(
		"SELECT * FROM tickets",
		conn
	)

	conn.close()

	return df

def add_ticket(
	customer,
	title,
	description,
	priority,
	response_due,
	assignee
):
	conn = get_connection()

	conn.execute("""
		INSERT INTO tickets
		(customer, title, description, priority, response_due,
		 assignee, status, created_at)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)
	""", (
		customer,
		title,
		description,
		priority,
		response_due.isoformat(),
		assignee if assignee != "Unassigned" else None,
		"Open",
		datetime.now().isoformat()
	))

	conn.commit()
	conn.close()

def update_ticket(ticket_id, status, assignee):
	conn = get_connection()

	conn.execute("""
		UPDATE tickets
		SET status = ?, assignee = ?
		WHERE id = ?
	""", (
		status,
		assignee if assignee != "Unassigned" else None,
		ticket_id
	))

	conn.commit()
	conn.close()

# -----------------------------
# Queue ordering
# -----------------------------
def calculate_queue(df):
	if df.empty:
		return df

	now = datetime.now()

	df = df.copy()

	df["response_due_dt"] = pd.to_datetime(df["response_due"])

	df["overdue"] = (
		(df["response_due_dt"] < now)
		& (df["status"] != "Resolved")
	)

	# Urgent gets higher priority than normal
	df["priority_rank"] = df["priority"].map({
		"Urgent": 0,
		"Normal": 1
	})

	# Overdue tickets are always surfaced first.
	# Then priority, then promised response time,
	# then creation time.
	df = df.sort_values(
		by=[
			"overdue",
			"priority_rank",
			"response_due_dt",
			"created_at"
		],
		ascending=[
			False,
			True,
			True,
			True
		]
	)

	return df

# -----------------------------
# UI
# -----------------------------
st.set_page_config(
	page_title="Support Queue",
	page_icon="🛠️",
	layout="wide"
)

init_db()

st.title("🛠️ Support Queue")
st.caption(
	"Helpdesk ticket management — keep the most pressing issue on top."
)

# -----------------------------
# Sidebar - Add ticket
# -----------------------------
with st.sidebar:
	st.header("➕ New Ticket")

	customer = st.text_input("Customer name")

	title = st.text_input("Ticket title")

	description = st.text_area(
		"Description"
	)

	priority = st.selectbox(
		"Priority",
		["Urgent", "Normal"]
	)

	response_hours = st.number_input(
		"Response time (hours)",
		min_value=1,
		max_value=48,
		value=2
	)

	assignee = st.selectbox(
		"Assign to",
		[
			"Unassigned",
			"Priya",
			"Arjun"
		]
	)

	if st.button(
		"Create Ticket",
		use_container_width=True
	):
		if not customer.strip() or not title.strip():
			st.error(
				"Customer name and ticket title are required."
			)
		else:
			due = datetime.now() + timedelta(
				hours=response_hours
			)

			add_ticket(
				customer,
				title,
				description,
				priority,
				due,
				assignee
			)

			st.success(
				"Ticket created successfully!"
			)

			st.rerun()

# -----------------------------
# Load and sort
# -----------------------------
tickets = load_tickets()

tickets = calculate_queue(tickets)

# -----------------------------
# Metrics
# -----------------------------
open_tickets = tickets[
	tickets["status"] != "Resolved"
]

urgent_count = len(
	open_tickets[
		open_tickets["priority"] == "Urgent"
	]
)

overdue_count = len(
	open_tickets[
		open_tickets["overdue"]
	]
)

resolved_count = len(
	tickets[
		tickets["status"] == "Resolved"
	]
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
	"Total Tickets",
	len(tickets)
)

col2.metric(
	"Open",
	len(open_tickets)
)

col3.metric(
	"Urgent",
	urgent_count
)

col4.metric(
	"Overdue",
	overdue_count
)

st.divider()

# -----------------------------
# Filters
# -----------------------------
st.subheader("Ticket Queue")

col1, col2, col3 = st.columns(3)

with col1:
	search = st.text_input(
		"🔎 Search",
		placeholder="Customer or ticket title"
	)

with col2:
	status_filter = st.selectbox(
		"Status",
		[
			"All",
			"Open",
			"In Progress",
			"Resolved"
		]
	)

with col3:
	assignee_filter = st.selectbox(
		"Assignee",
		[
			"All",
			"Unassigned",
			"Priya",
			"Arjun"
		]
	)

# Apply filters
filtered = tickets.copy()

if search:
	search_lower = search.lower()

	filtered = filtered[
		filtered["customer"].str.lower().str.contains(
			search_lower,
			na=False
		)
		|
		filtered["title"].str.lower().str.contains(
			search_lower,
			na=False
		)
	]

if status_filter != "All":
	filtered = filtered[
		filtered["status"] == status_filter
	]

if assignee_filter != "All":

	if assignee_filter == "Unassigned":
		filtered = filtered[
			filtered["assignee"].isna()
		]
	else:
		filtered = filtered[
			filtered["assignee"] == assignee_filter
		]

st.caption(
	f"Showing {len(filtered)} ticket(s)"
)

# -----------------------------
# Display tickets
# -----------------------------
if filtered.empty:

	st.info(
		"No tickets match the selected filters."
	)

else:

	for _, ticket in filtered.iterrows():

		due = pd.to_datetime(
			ticket["response_due"]
		)

		now = datetime.now()

		is_overdue = (
			due.to_pydatetime() < now
			and ticket["status"] != "Resolved"
		)

		if ticket["priority"] == "Urgent":
			priority_icon = "🔴"
		else:
			priority_icon = "🟡"

		if is_overdue:
			deadline_text = "⚠️ OVERDUE"
		else:
			remaining = due.to_pydatetime() - now

			total_seconds = int(
				remaining.total_seconds()
			)

			hours = total_seconds // 3600
			minutes = (
				total_seconds % 3600
			) // 60

			if hours > 0:
				deadline_text = (
					f"{hours}h {minutes}m remaining"
				)
			else:
				deadline_text = (
					f"{minutes}m remaining"
				)

		with st.container(border=True):

			col1, col2 = st.columns(
				[5, 2]
			)

			with col1:

				st.markdown(
					f"### {priority_icon} "
					f"#{int(ticket['id'])} "
					f"{ticket['title']}"
				)

				st.write(
					f"**Customer:** {ticket['customer']}"
				)

				if ticket["description"]:
					st.write(
						ticket["description"]
					)

				st.caption(
					f"Created: "
					f"{pd.to_datetime(ticket['created_at']).strftime('%d %b %Y %H:%M')}"
				)

			with col2:

				st.markdown(
					f"**Priority:** "
					f"{ticket['priority']}"
				)

				st.markdown(
					f"**Deadline:** "
					f"{deadline_text}"
				)

				display_assignee = (
					"Unassigned"
					if pd.isna(ticket["assignee"])
					else str(ticket["assignee"])
				)

				st.markdown(
					f"**Assigned:** {display_assignee}"
				)

				st.markdown(
					f"**Status:** "
					f"{ticket['status']}"
				)

			st.divider()

			edit_col1, edit_col2, edit_col3 = st.columns(3)

			with edit_col1:

				new_status = st.selectbox(
					"Update status",
					[
						"Open",
						"In Progress",
						"Resolved"
					],
					index=[
						"Open",
						"In Progress",
						"Resolved"
					].index(ticket["status"]),
					key=f"status_{ticket['id']}"
				)

			with edit_col2:

				raw_assignee = ticket["assignee"]

				if pd.isna(raw_assignee) or not str(raw_assignee).strip():
					current_assignee = "Unassigned"
				else:
					current_assignee = str(raw_assignee)

				new_assignee = st.selectbox(
					"Assign",
					[
						"Unassigned",
						"Priya",
						"Arjun"
					],
					index=[
						"Unassigned",
						"Priya",
						"Arjun"
					].index(current_assignee),
					key=f"assignee_{ticket['id']}"
				)

			with edit_col3:

				if st.button(
					"Save Changes",
					key=f"save_{ticket['id']}"
				):

					update_ticket(
						int(ticket["id"]),
						new_status,
						new_assignee
					)

					st.success(
						"Updated!"
					)

					st.rerun()
