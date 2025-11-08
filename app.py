import gradio as gr
import json
import requests
from datetime import datetime
import os

class HomeschoolCurriculumGenerator:
    def __init__(self):
        self.api_url = "https://api.anthropic.com/v1/messages"
        # Get API key from Hugging Face Secrets
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    def get_grade_suffix(self, grade):
        """Return the appropriate suffix for grade numbers"""
        grade = int(grade)
        if grade == 1:
            return 'st'
        elif grade == 2:
            return 'nd'
        elif grade == 3:
            return 'rd'
        else:
            return 'th'
    
    def generate_curriculum(self, student_name, grade_level, selected_subjects, 
                          learning_style, weeks_per_year, days_per_week, goals=""):
        """Generate curriculum using Claude API"""
        
        if not selected_subjects or len(selected_subjects) == 0:
            return "❌ Please select at least one subject", None
        
        if not self.api_key:
            return "❌ API key not configured. Please add ANTHROPIC_API_KEY to Hugging Face Secrets.", None
        
        # Convert selected subjects list to string
        subjects_str = ', '.join(selected_subjects)
        
        prompt = f"""Create a detailed homeschool curriculum plan for a {grade_level}{self.get_grade_suffix(grade_level)} grade student named {student_name or 'Student'}.

Subjects to cover: {subjects_str}
Learning style: {learning_style}
Academic year: {weeks_per_year} weeks, {days_per_week} days per week
{f'Learning goals: {goals}' if goals else ''}

Please provide:
1. A brief overview of what this grade level student should learn
2. For each subject:
   - Key learning objectives
   - Recommended weekly time allocation
   - Sample activities tailored to {learning_style} learning style
   - Assessment methods
   - Resource suggestions (books, websites, materials)
3. A sample weekly schedule

Format your response as structured JSON with this exact format:
{{
  "overview": "string",
  "subjects": [
    {{
      "name": "string",
      "objectives": ["string"],
      "weeklyHours": number,
      "activities": ["string"],
      "assessments": ["string"],
      "resources": ["string"]
    }}
  ],
  "weeklySchedule": [
    {{
      "day": "Monday",
      "periods": [
        {{"time": "9:00-10:00", "subject": "Math", "activity": "string"}}
      ]
    }}
  ]
}}

Respond ONLY with valid JSON, no other text."""

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            text = result['content'][0]['text']
            
            # Clean up potential markdown formatting
            clean_text = text.replace('```json', '').replace('```', '').strip()
            curriculum_data = json.loads(clean_text)
            
            # Format for display
            formatted_output = self.format_curriculum_display(curriculum_data, student_name, grade_level)
            
            # Format for download
            download_text = self.format_curriculum_text(curriculum_data, student_name, grade_level)
            
            return formatted_output, download_text
            
        except requests.exceptions.RequestException as e:
            return f"❌ API request failed: {str(e)}", None
        except json.JSONDecodeError as e:
            return f"❌ Failed to parse curriculum data: {str(e)}", None
        except Exception as e:
            return f"❌ Error: {str(e)}", None
    
    def format_curriculum_display(self, curriculum, student_name, grade_level):
        """Format curriculum for display in Gradio"""
        
        output = f"""# 📚 Homeschool Curriculum
**Student:** {student_name or 'Student'}  
**Grade:** {grade_level}  
**Generated:** {datetime.now().strftime('%Y-%m-%d')}

---

## 🎯 Overview
{curriculum['overview']}

---

## 📖 Subject Plans

"""
        
        for subject in curriculum['subjects']:
            output += f"""### {subject['name']} ({subject['weeklyHours']} hrs/week)

**Objectives:**
"""
            for i, obj in enumerate(subject['objectives'], 1):
                output += f"{i}. {obj}\n"
            
            output += "\n**Activities:**\n"
            for act in subject['activities']:
                output += f"- {act}\n"
            
            output += "\n**Assessments:**\n"
            for ass in subject['assessments']:
                output += f"- {ass}\n"
            
            output += "\n**Resources:**\n"
            for res in subject['resources']:
                output += f"- {res}\n"
            
            output += "\n---\n\n"
        
        output += "## 📅 Sample Weekly Schedule\n\n"
        for day in curriculum['weeklySchedule']:
            output += f"### {day['day']}\n"
            for period in day['periods']:
                output += f"**{period['time']}** - *{period['subject']}:* {period['activity']}\n"
            output += "\n"
        
        return output
    
    def format_curriculum_text(self, curriculum, student_name, grade_level):
        """Format curriculum as plain text for download"""
        
        output = f"""HOMESCHOOL CURRICULUM
Student: {student_name or 'Student'}
Grade: {grade_level}
Generated: {datetime.now().strftime('%Y-%m-%d')}

{curriculum['overview']}

SUBJECTS:
"""
        
        for subject in curriculum['subjects']:
            output += f"\n{subject['name']}\n"
            output += f"Weekly Hours: {subject['weeklyHours']}\n\n"
            
            output += "Objectives:\n"
            for i, obj in enumerate(subject['objectives'], 1):
                output += f"{i}. {obj}\n"
            
            output += "\nActivities:\n"
            for act in subject['activities']:
                output += f"- {act}\n"
            
            output += "\nAssessments:\n"
            for ass in subject['assessments']:
                output += f"- {ass}\n"
            
            output += "\nResources:\n"
            for res in subject['resources']:
                output += f"- {res}\n"
            
            output += "\n" + "-"*50 + "\n"
        
        output += "\nWEEKLY SCHEDULE:\n"
        for day in curriculum['weeklySchedule']:
            output += f"\n{day['day']}:\n"
            for period in day['periods']:
                output += f"  {period['time']} - {period['subject']}: {period['activity']}\n"
        
        return output

# Initialize generator
generator = HomeschoolCurriculumGenerator()

# Define Gradio interface
def generate_curriculum_gradio(student_name, grade_level, math, reading, science, social_studies, 
                               art, music, pe, language, learning_style, weeks, days, goals):
    """Wrapper function for Gradio interface"""
    
    # Build selected subjects list
    subject_map = {
        math: "Math",
        reading: "Reading/Language Arts",
        science: "Science",
        social_studies: "Social Studies",
        art: "Art",
        music: "Music",
        pe: "Physical Education",
        language: "Foreign Language"
    }
    
    selected_subjects = [subject_map[key] for key in subject_map if key]
    
    display_output, download_text = generator.generate_curriculum(
        student_name=student_name,
        grade_level=grade_level,
        selected_subjects=selected_subjects,
        learning_style=learning_style,
        weeks_per_year=weeks,
        days_per_week=days,
        goals=goals
    )
    
    return display_output, download_text

# Create Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), title="Homeschool Curriculum Generator") as demo:
    gr.Markdown("""
    # 📚 Homeschool Curriculum Generator
    Create a personalized curriculum plan tailored to your student's needs using AI
    """)
    
    with gr.Row():
        with gr.Column():
            student_name = gr.Textbox(
                label="Student Name (optional)",
                placeholder="Enter student name"
            )
            
            grade_level = gr.Dropdown(
                choices=[str(i) for i in range(1, 13)],
                label="Grade Level",
                value="5"
            )
            
            gr.Markdown("### Select Subjects")
            with gr.Row():
                with gr.Column():
                    math = gr.Checkbox(label="Math", value=True)
                    reading = gr.Checkbox(label="Reading/Language Arts", value=True)
                    science = gr.Checkbox(label="Science", value=True)
                    social_studies = gr.Checkbox(label="Social Studies", value=True)
                with gr.Column():
                    art = gr.Checkbox(label="Art")
                    music = gr.Checkbox(label="Music")
                    pe = gr.Checkbox(label="Physical Education")
                    language = gr.Checkbox(label="Foreign Language")
            
            learning_style = gr.Dropdown(
                choices=[
                    "visual",
                    "auditory",
                    "kinesthetic",
                    "reading"
                ],
                label="Primary Learning Style",
                value="visual"
            )
            
            with gr.Row():
                weeks = gr.Number(
                    label="Weeks per Year",
                    value=36,
                    minimum=1,
                    maximum=52
                )
                days = gr.Number(
                    label="Days per Week",
                    value=5,
                    minimum=1,
                    maximum=7
                )
            
            goals = gr.Textbox(
                label="Learning Goals (optional)",
                placeholder="Any specific goals or focus areas for this student?",
                lines=3
            )
            
            generate_btn = gr.Button("✨ Generate Curriculum", variant="primary", size="lg")
    
    with gr.Row():
        with gr.Column():
            output_display = gr.Markdown(label="Curriculum")
            download_file = gr.File(label="Download Curriculum")
    
    # Set up event handler
    def generate_and_save(student_name, grade_level, math, reading, science, social_studies, 
                         art, music, pe, language, learning_style, weeks, days, goals):
        display, text = generate_curriculum_gradio(
            student_name, grade_level, math, reading, science, social_studies,
            art, music, pe, language, learning_style, weeks, days, goals
        )
        
        if text:
            # Save to file
            filename = f"{student_name or 'student'}-curriculum.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            return display, filename
        else:
            return display, None
    
    generate_btn.click(
        fn=generate_and_save,
        inputs=[student_name, grade_level, math, reading, science, social_studies,
               art, music, pe, language, learning_style, weeks, days, goals],
        outputs=[output_display, download_file]
    )
    
    gr.Markdown("""
    ---
    ### 📝 Instructions:
    1. Fill in the student information
    2. Select subjects to include in the curriculum
    3. Choose the primary learning style
    4. Set schedule parameters (weeks per year, days per week)
    5. Optionally add specific learning goals
    6. Click "Generate Curriculum" to create a personalized plan
    7. Download the curriculum as a text file
    
    **Note:** You'll need to add your Anthropic API key to the Hugging Face Spaces secrets as `ANTHROPIC_API_KEY`
    """)

if __name__ == "__main__":
    demo.launch()