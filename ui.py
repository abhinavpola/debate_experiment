import streamlit as st
import pandas as pd
import ast
import json
# Load the data
@st.cache_data
def load_data():
    df = pd.read_csv("debate_conversational_5_turns.csv")
    # Safely convert string representation of list to actual list
    return df

def save_data(df):
    # Convert lists back to strings before saving
    df_to_save = df.copy()
    df_to_save.to_csv("debate.csv", index=False)
    st.success("Changes saved successfully!")

# Main app
st.title("Debate Agent Votes Editor")

# Load the data
df = load_data()

# Create a selector for debate topic
debate_topic = st.selectbox("Select Debate Topic", df["Topic"].unique())

# Create a selector for debate number
debate_number = st.selectbox("Select Debate Number", df[df["Topic"] == debate_topic]["Debate Number"].unique())

# Get the selected row
row = df[(df["Debate Number"] == debate_number) & (df["Topic"] == debate_topic)].iloc[0]

# Display debate information
st.subheader("Debate Information")
st.write(f"Topic: {row['Topic']}")
st.write(f"Winner: {row['Winner']}")

# Create a text input for editing votes
current_votes = row["Agent Votes"]
st.subheader("Edit Agent Votes")
st.write("Current votes (one per line):")

# Create a text area with votes, one per line
votes_text = st.text_area(
    "Edit votes below:",
    value=str(current_votes).replace("'", '"'),
    height=200,
    key=f"votes_{debate_number}"
)

# Create a save button
if st.button("Save Changes"):
    # Convert the text area content to a json string
    new_votes = json.loads(votes_text.replace("'", '"'))
    
    # Update the dataframe
    df.loc[(df["Debate Number"] == debate_number) & (df["Topic"] == debate_topic), "Agent Votes"] = json.dumps(new_votes)
    
    # Save the changes
    save_data(df)
