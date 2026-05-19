# Mergington High School Activities API

A FastAPI application that allows anyone to view activities while only authenticated staff can manage registrations.

## Features

- View all available extracurricular activities
- Staff login/logout with role-aware permissions
- Staff-only registration and unregister actions

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Run the application:

   ```
   uvicorn app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                     | Login as staff user and receive bearer token                        |
| POST   | `/auth/logout`                                                    | Logout current staff session                                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teacher/admin only)                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher/admin only)                        |

## Staff Credentials

- Credentials are loaded from `staff_users.json`.
- You can configure a different credentials file using the `STAFF_CREDENTIALS_FILE` environment variable.
- The credentials file format is:

   ```json
   {
      "users": [
         {"username": "teacher.alex", "password": "changeme-teacher", "role": "teacher"},
         {"username": "admin.riley", "password": "changeme-admin", "role": "admin"}
      ]
   }
   ```

## Tests

Run backend tests with:

```
pytest
```

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity data and login sessions are stored in memory, which means data will be reset when the server restarts.
