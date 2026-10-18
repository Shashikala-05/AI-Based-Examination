# Milestone 2 — UI/UX Redesign with SQLite

This version focuses on alignment, spacing, consistent form controls, responsive layout,
clear labels, validation feedback, and a role-specific sign-in experience.

## Files
- `app.py`: Streamlit UI and SQLite backend
- `requirements.txt`: dependencies
- `README.md`: setup notes

## Install and run (Windows / VS Code)
```cmd
cd "C:\Users\Shara\OneDrive\Desktop\Projects\AI-Based Examination"
venv\Scripts\activate
pip install -r milestone2\requirements.txt
cd milestone2
streamlit run app.py
```

## Admin registration
Admin signup is protected by an environment variable. In Command Prompt, set it before
starting Streamlit:
```cmd
set ADMIN_SIGNUP_CODE=choose-a-long-private-code
streamlit run app.py
```
Enter that code only in the Admin signup form. Do not commit it to GitHub.

## Database
`exam_portal.db` is created automatically inside this folder.
The application stores password hashes and salts, not plain-text passwords.

## Notes
This milestone implements authentication and role-specific welcome pages. Connect exam
creation, question management, results and admin user-management modules in later steps.
For production deployment, add HTTPS, rate limiting, account recovery, audit logging,
and controlled admin provisioning.
