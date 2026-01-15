# SenioCare — Ollama Tool Calling (Mock Data)

This project demonstrates **Pseudo Tool Calling** with an Ollama local model (e.g., `seniocare_med42:latest`) and local Python functions that read from mock data.

---
## 1) Folder Structure

Make sure your folder looks like this:

Tool Calling (1)/
- functions.py
- mock_data.json
- ollama_integration.py
- README.md
- requirements.txt
- run.bat

## Files Description
- `mock_data.json`: Mock data for users, foods, etc.
- `functions.py`: Tool functions for the app.
- `ollama_integration.py`: Main chat logic with pseudo tool calling.
- `requirements.txt`: Python dependencies.
- `run.bat`: Windows batch script to run the project.
- `README.md`: Project documentation.
---

## 2) Prerequisites

### Python
- Install Python 3.13 or higher from [python.org](https://www.python.org/downloads/).
- Ensure `python` command is available in your terminal/command prompt.

### Ollama
- Download and install Ollama from [ollama.com](https://ollama.com/).

- Install the required model: Open a terminal and run `ollama pull thewindmom/llama3-med42-8b:latest`, then customize it to create `seniocare_med42:latest`, and run `ollama run seniocare_med42:latest`.

- Start the Ollama service: Run `ollama serve` in a terminal (keep it running in the background).

Verify the model is available: `ollama list` should show `seniocare_med42:latest`.

---
## 3) Running the Project

- Don't forget to make sure from OLLAMA_URL and MODEL_NAME Variables in ollama_integration.py are correct.

### Easy Way (Recommended)
- In Terminal:
  - `.\run.bat` to set up the environment and start the chat.

### Manual Way
In Terminal:
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (on Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python ollama_integration.py`
---
## 4) How It Works

- The app starts a chat interface.
- You can ask questions related to user profiles, food search, drug interactions, etc.
- The Ollama model decides if a tool is needed and calls local Python functions from `functions.py` using mock data from `mock_data.json`.
- Type 'exit' or 'x' to quit the chat.

### Example Interactions

**Example 1: Drug-Food Interaction Check**
You: Can user 1 eat White Rice while taking Metformin?

Tool requested: check_drug_food_interactions
Args: {'user_id': 1, 'food_name': 'White Rice'}

SenioCare:
Based on our analysis, it is recommended to avoid consuming high-carbohydrate foods like white rice when taking metformin as they can potentially decrease its effectiveness in managing blood sugar levels. Please consult your healthcare provider for personalized dietary advice regarding medications and meal choices.

The above information was obtained using SenioCare's check_drug_food_interactions tool with the provided inputs: User ID - 1; Food Name - White Rice. The resulting interaction report indicated a risk level of 'avoid' due to potential adverse effects on medication efficacy. Therefore, we have advised against this food choice based on available data. If you require further clarification or additional guidance tailored specifically to your health situation, kindly schedule an appointment with your doctor or registered dietitian. 

--

**Example 2: Meal Plan Suggestion**
You: Hello, can you also suggest a meal plan for user 1?

Tool requested: suggest_meal_plan_for_user
Args: {'user_id': 1}

SenioCare:
Based on your dietary needs and preferences as indicated by your profile, we recommend meals such as Greek yogurt with apple slices for breakfast, grilled fish paired with brown rice at lunchtime, and chicken breast accompanied by vegetables during dinner to help manage Diabetes effectively. Please consult with your healthcare provider before making any significant changes to your diet.

Would you like more information about this suggested meal plan or would you prefer exploring other options tailored specifically for you?

--

**Example 3: Product Analysis**
You: Analyze product Wonder Bread

Tool requested: analyze_product
Args: {'product_name': 'Wonder Bread'}

SenioCare:
The analysis shows that Wonder Bread has moderate nutritional impact and is considered acceptable for consumption as part of a balanced diet. It contains 150 calories per slice with 30 total carbs, including 2 grams of fiber and 10 grams of sugars without added sugars. Each serving provides 4 grams of protein and 260 milligrams of sodium. Overall, it's an average choice to consider when choosing bread options but may not be ideal due to its relatively high carb content. Considering alternatives or portion control could help balance your daily intake better. 

--

**Example 4: Greeting (No Tool Needed)**

You: hello

Tool requested: no_tool
Args: {'answer': "Hello! This is the SenioCare Tool Router. I'm here to help with your query."}

SenioCare:

❌ Error: Unknown tool: no_tool 


