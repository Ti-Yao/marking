import streamlit as st
import pandas as pd
import numpy as np
import os
import re

def format_string(string):
    if len(string.replace('\n', '')) > 90:
        # Split the string at the closest space to the 90 characters mark
        formatted_string = re.sub(r'(.{1,90})\s', r'\1\n', string)
        return formatted_string
    else:
        return string

# Constants
root_folder = '.'
marking_groups_path = f'{root_folder}/reference/Marking Groups.xlsx'
results_path = f'{root_folder}/results/scores_VM.csv'

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

# Initialize the results DataFrame if it doesn't exist
if not os.path.isfile(results_path):
    results = pd.DataFrame()
    results['ID'] = candidates
    for q in questions:
        results[q] = '-'
    results.to_csv(results_path, index=False)

# Load the results CSV
results = pd.read_csv(results_path)

# Function to get unmarked responses for a question
def get_unmarked(question):
    unmarked = list(results[question].values).count('-')
    return unmarked

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

# Reload results and marks for the selected question
results = pd.read_csv(results_path)  # Re-read the CSV file when the question changes

# Safely update session state with marks for the selected question
st.session_state.marks_selected = {
    candidate: results.loc[results['ID'] == int(candidate), selected_question].values[0]
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

# Button to save results
if st.button("Save Marks"):
    # Update the marks in the results DataFrame
    for candidate, mark in st.session_state.marks_selected.items():
        results.loc[results['ID'] == int(candidate), selected_question] = mark
    
    # Write the updated results back to the CSV file
    results.to_csv(results_path, index=False)
    st.success(f"Marks for {selected_question} have been saved!")
    st.dataframe(results)

# Display remaining unmarked questions
questions_left = [q for q in questions if get_unmarked(q) > 0]
st.write(f"Remaining Unmarked Questions: {len(questions_left)}/{len(questions)}")
st.write(", ".join(questions_left))
