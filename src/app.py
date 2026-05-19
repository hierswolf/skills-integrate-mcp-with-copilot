"""
High School Management System API

A super simple FastAPI application that allows users to view activities and
authenticated staff to manage extracurricular registrations.
"""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import json
import os
from pathlib import Path
import secrets

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


# Allowed roles for registration changes.
ALLOWED_MUTATION_ROLES = {"teacher", "admin"}


def load_staff_users() -> dict[str, dict[str, str]]:
    """Load staff credentials from configurable JSON file."""
    default_path = current_dir / "staff_users.json"
    credentials_path = Path(os.getenv("STAFF_CREDENTIALS_FILE", default_path))

    try:
        with credentials_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"Staff credentials file not found: {credentials_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON in staff credentials file: {credentials_path}"
        ) from exc

    users = data.get("users", [])
    staff_users = {}
    for user in users:
        username = user.get("username")
        password = user.get("password")
        role = user.get("role")

        if not username or not password or not role:
            continue

        staff_users[username] = {
            "password": password,
            "role": role
        }

    if not staff_users:
        raise RuntimeError("No valid staff users configured")

    return staff_users

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

staff_users = load_staff_users()

# In-memory auth session store for demo purposes.
active_tokens: dict[str, dict[str, str]] = {}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> dict[str, str]:
    """Resolve bearer token to a logged-in staff session."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    token = credentials.credentials
    session = active_tokens.get(token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    return session


def require_staff_role(
    session: dict[str, str] = Depends(get_current_session)
) -> dict[str, str]:
    """Allow only teacher/admin roles to mutate registrations."""
    role = session.get("role", "")
    if role not in ALLOWED_MUTATION_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    return session


@app.post("/auth/login")
def login(payload: LoginRequest):
    user = staff_users.get(payload.username)
    if user is None or user["password"] != payload.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = secrets.token_urlsafe(32)
    active_tokens[token] = {
        "username": payload.username,
        "role": user["role"]
    }

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "username": payload.username
    }


@app.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    _: dict[str, str] = Depends(get_current_session)
):
    if credentials is not None:
        active_tokens.pop(credentials.credentials, None)

    return {"message": "Logged out successfully"}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _: dict[str, str] = Depends(require_staff_role)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _: dict[str, str] = Depends(require_staff_role)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
