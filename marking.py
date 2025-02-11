import streamlit as st
import pandas as pd
import numpy as np
import re
from streamlit_gsheets import GSheetsConnection

def format_string(string):
    if len(string.replace('\n', '')) > 90:
        # Split the string at the closest space to the 90 characters mark
        formatted_string = re.sub(r'(.{1,90})\s', r'\1\n', string)
        return formatted_string
    else:
        return string

# Google Sheets URL
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1AYNUeyKcEIa5qYQD83HwX6iLItMhbpmZPeDgxJq-bm8/edit?usp=sharing"

# Setup Google Sheets connection (using a public Google Sheet for read-write)
conn = st.connection("gsheets", type=GSheetsConnection)

# Read your Google Sheets data into DataFrame
df_results = conn.read(spreadsheet=spreadsheet_url)

# Constants
root_folder = '.'
marking_groups_path = f'{root_folder}/reference/Marking Groups.xlsx'

# Load marking groups data
marking_groups = pd.read_excel(marking_groups_path).iloc[2:]
marking_groups.columns = ['Q', 'mark', 'marker1', 'marker2']
Marker_Initials = 'VM'
question_selection = marking_groups.loc[(marking_groups['marker1'] == Marker_Initials) | (marking_groups['marker2'] == Marker_Initials)].Q.values

# Load the formatted responses and other necessary data
formatted_reponses = pd.read_csv(f'{root_folder}/reference/formatted_reponses.csv', index_col=0)
questions = list(formatted_reponses.columns)
questions = [q for q in questions if int(q.split('Q')[-1].split('.')[0]) in question_selection]
formatted_reponses = formatted_reponses[questions]
candidates = formatted_reponses.drop(['score', 'answer']).astype(str).index
scores = formatted_reponses.loc['score']
answers = formatted_reponses.loc['answer']
responses = formatted_reponses.drop(['score', 'answer'])

# Initialize session state if not already initialized
if 'marks_selected' not in st.session_state:
    st.session_state.marks_selected = {candidate: '-' for candidate in candidates}

if 'selected_question' not in st.session_state:
    st.session_state.selected_question = questions[0]  # Set default selected question

# Streamlit UI
st.title("Marking Interface")
st.subheader(f"Marker: {Marker_Initials}")

# Display questions
question_selection_str = ', '.join(str(x) for x in question_selection)
st.write(f"You are marking the following questions: {question_selection_str}")

# Select current question
selected_question = st.selectbox("Select a Question", questions, index=questions.index(st.session_state.selected_question))
st.session_state.selected_question = selected_question  # Update session state with selected question

# Reload results from Google Sheets for the selected question
df_results = conn.read(spreadsheet=spreadsheet_url)

# Safely update session state with marks for the selected question
st.session_state.marks_selected = {
    candidate: df_results.loc[df_results['ID'] == int(candidate), selected_question].values[0]
    for candidate in candidates
}

# Display question and answer
st.write(f"### Question: {selected_question}")
st.write(format_string(formatted_reponses[selected_question].iloc[0]))  # Show formatted question
st.write(f"### Answer:")
st.write(answers[selected_question].replace('(2)', '(2)\n'))  # Show formatted answer

# Display candidates and their responses
responses_for_question = responses[selected_question]

# Candidate dropdowns for marking
marks = ['-'] + [str(val) for val in np.arange(0, float(scores[selected_question]) + 0.5, 0.5)]

# Ensure the marks are updated when the question changes
for candidate in candidates:
    candidate_response = responses_for_question.loc[candidate]
    candidate_response = format_string(candidate_response.replace('\n', ' ').replace('\t', ' '))
    
    st.write(f"Candidate {candidate}:")
    st.write(candidate_response)
    
    # Use the stored mark from session_state or default to '-'
    mark = st.session_state.marks_selected.get(candidate, '-')
    
    # Dropdown for marking
    mark = st.selectbox(f"Mark for {candidate}", options=marks, index=marks.index(str(mark)), key=f"{candidate}_{selected_question}")
    
    # Update session state with the selected mark
    st.session_state.marks_selected[candidate] = mark

# Button to save results to Google Sheets
if st.button("Save Marks"):
    # Update the marks in the results DataFrame
    for candidate, mark in st.session_state.marks_selected.items():
        df_results.loc[df_results['ID'] == int(candidate), selected_question] = mark
    
    # Write the updated results back to Google Sheets
    conn.write(spreadsheet=spreadsheet_url, dataframe=df_results)
    st.success(f"Marks for {selected_question} have been saved to Google Sheets!")
    st.dataframe(df_results)

# Display remaining unmarked questions
def get_unmarked(question):
    unmarked = list(df_results[question].values).count('-')
    return unmarked

questions_left = [q for q in questions if get_unmarked(q) > 0]
st.write(f"Remaining Unmarked Questions: {len(questions_left)}/{len(questions)}")
st.write(", ".join(questions_left))
