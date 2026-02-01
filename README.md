# HW7 – AI-Powered Travel Guide  
**Author:** Faraz Shamim  

## Project Purpose
This project is an AI-assisted Travel Guide application designed to help users generate personalized travel itineraries based on their preferences. The application demonstrates how AI can be used to automate planning tasks that traditionally require manual research and decision-making.

The project applies AI-assisted workflows by collecting structured user input and leveraging a large language model to generate customized, multi-day travel plans.

## What the Application Does
The Travel Guide application allows users to input:
- Travel destination
- Number of days for the trip
- Personal interests (e.g., museums, food, nightlife, nature)
- Guardrails or constraints (e.g., kid-friendly activities, wheelchair accessibility, no walking tours)

Using these inputs, the application:
- Generates a complete day-by-day travel itinerary
- Organizes activities for each day of the trip
- Produces a downloadable PDF version of the travel plan
- Provides a reset option to generate a new plan

The application uses AI-generated responses to dynamically adapt plans based on user preferences, demonstrating real-world AI-assisted decision support.

## AI & Technology Used
- Python
- Streamlit for the user interface
- OpenAI API for AI-generated itinerary planning
- Prompt engineering to guide AI output
- PDF generation for professional output delivery

## How to Run the Application
1. Ensure Python is installed
2. Install required dependencies
3. Run the application using Streamlit:

```bash
python -m streamlit run TravelGuide.py
