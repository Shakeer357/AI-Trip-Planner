import os
import requests
import json
import re
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_plan_from_llm(destination, days, people, interests, age_group, budget):
    """Sends a comprehensive prompt to the Gemini LLM and gets a travel plan."""
    if not GEMINI_API_KEY:
        return {"error": "API Key is not configured. Please get a key from Google AI Studio."}

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={GEMINI_API_KEY}"
    
  
    prompt = f"""
    You are an expert travel planner. Your task is to generate a creative and practical travel itinerary and respond ONLY in a clean JSON format. DO NOT include any text before or after the JSON object.

    Generate a day-by-day itinerary for the following trip:
    - Destination: {destination}
    - Duration: {days} days
    - Travelers: {people} people
    - Age Group: {age_group}
    - Interests: {interests}
    - Budget Style: {budget}

    The JSON output must be an object with a single key "plan".
    The value of "plan" must be an array of objects, one for each day.
    Each day object in the array MUST contain exactly these four keys. DO NOT skip any of them.
    1. "day": (Number) The day number.
    2. "activities": (String) A short summary of places for the day.
    3. "description": (String) A detailed and engaging paragraph describing the day's plan. Include suggestions for meals (like breakfast, lunch, and dinner) and mention typical travel times between major activities based on your knowledge of the city's traffic.
    4. "estimated_cost": (String) THIS IS MANDATORY. Provide a specific cost estimate for the day's activities, formatted like "₹3,500" or "$150".
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # Extract the text and clean it up
        api_response_text = response.json()['candidates'][0]['content']['parts'][0]['text']
        api_response_text = api_response_text.strip().replace("```json", "").replace("```", "")
        return json.loads(api_response_text)
    except Exception as e:
        print(f"LLM Error: {e}")
        return {"error": "Failed to generate a valid plan from the AI. The AI response may not have been in the correct JSON format."}

@app.route("/", methods=["GET", "POST"])
def home():
    plan_data = None
    destination_name = ""
    if request.method == "POST":
        destination_name = request.form.get("destination")
        days = int(request.form.get("duration", 1))
        people = int(request.form.get("people", 1))
        age_group = request.form.get("age_group")
        interests = request.form.get("interests")
        budget = request.form.get("budget")

        plan_data = get_plan_from_llm(destination_name, days, people, interests, age_group, budget)
        
        # Calculate the grand total after getting the plan from the AI
        if plan_data and 'plan' in plan_data:
            grand_total = 0
            for day in plan_data['plan']:
                cost_string = day.get("estimated_cost", "0")
                # Find all numbers in the cost string and take the first one
                cost_numbers = re.findall(r'\d+', cost_string.replace(',', ''))
                if cost_numbers:
                    grand_total += int(cost_numbers[0])
            plan_data['grand_total'] = f"₹{grand_total:,}" # Format with commas

    return render_template("index.html", plan_data=plan_data, destination=destination_name)

if __name__ == "__main__":
    app.run(debug=True, port=5001)

