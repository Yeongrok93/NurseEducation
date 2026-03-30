# NurseEducation

NurseEducation is a research-oriented ICU communication simulation for SBAR training.
The application lets a nurse report a patient case turn by turn, receives physician responses, evaluates the cumulative SBAR report, and stores session logs in Supabase.

## What It Does

- Runs a Flask-based web simulation
- Uses scenario data stored in JSON
- Evaluates cumulative SBAR reporting with OpenAI
- Simulates physician follow-up questions and responses
- Requires login through Supabase Auth
- Stores session and interaction logs in Supabase

## Current Flow

1. User logs in through Supabase Auth
2. Flask verifies the Supabase access token and creates a server session
3. A new game session starts from a predefined scenario
4. The nurse sends messages across turns
5. The evaluator scores the cumulative report history, not only the latest turn
6. The physician agent responds based on missing, verified, and incorrect items
7. Logs are stored in Supabase tables

## Project Structure

- `app.py`: Flask entry point, auth/session handling, game routes, evaluation flow
- `engine/evaluator.py`: cumulative SBAR checklist evaluator
- `engine/physician_agent.py`: physician response generation based on evaluation output
- `engine/game_state.py`: turn progression, score state, success/time-over logic
- `engine/scenario_loader.py`: scenario loading and normalization
- `engine/log_repository.py`: Supabase logging layer
- `scenarios/`: scenario JSON files
- `templates/`: HTML templates for login and game UI
- `static/`: image assets
- `supabase/`: SQL and Supabase-related setup files

## Evaluation Logic

The app now uses cumulative evaluation across the full nurse report history.

Scored items:

- `identify_self`
- `patient_name`
- `situation`
- `context`
- `recent_findings`
- `facts_only`
- `assessment`
- `recommendation`
- `contact_information`

Notes:

- `patient_identifier` has been removed
- `total_score` is recalculated on the server
- greetings or short non-clinical messages are forced to low scores by server guardrails
- success requires both a high score and a clinically acceptable evaluation state

## Success Condition

A session is marked as `SUCCESS` only when all of the following are true:

- cumulative score is at least 8 out of 9
- `overall_status == "ready_for_action"`
- `incorrect_items` is empty

If turns run out first, the result is `TIME_OVER`.

## Authentication

The project uses Supabase Auth for login.

- Frontend uses `SUPABASE_ANON_KEY`
- Flask verifies the access token server-side
- User identity is stored in the Flask session
- Session logs are linked to the authenticated Supabase user id

## Logging

The app stores data in Supabase.

Current logging concept:

- `sessions`: one row per play session
- `interactions`: one row per turn

Stored data includes:

- user id
- scenario name
- start/end time
- nurse input
- physician response
- evaluator output
- patient state snapshot
- current nurse/game state

## Requirements

- Python 3.10+
- OpenAI API key
- Supabase project with Auth enabled
- Supabase logging tables configured

## Environment Variables

Create a `.env` file in the project root.

```env
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_flask_secret
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
```

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the server:

```bash
python app.py
```

Open in browser:

```text
http://127.0.0.1:5000
```

## Notes

- `.env`, research materials, and local notebooks should not be committed
- game state is currently stored in memory, so a server restart resets active sessions
- some UI text was hardened using HTML entities due to prior encoding issues

## Suggested Next Work

- add a cleaner Korean UI pass across the full template
- add user profile / research user mapping tables in Supabase
- add leaderboard and per-user history views
- add stronger scenario-specific validation rules beyond LLM evaluation
