from google.oauth2 import credentials
SCOPES = [
    "https://www.googleapis.com/auth/classroom.courses",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.announcements",
    "https://www.googleapis.com/auth/classroom.rosters",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly",
    "https://www.googleapis.com/auth/forms.body",
    "openid"
]
def check_scopes(creds):
    if creds.scopes and 'https://www.googleapis.com/auth/userinfo.email' in creds.scopes:
        print("Scope для email присутствует!")
    else:
        print("Scope для email отсутствует! Необходимо обновить credentials.")

# ... (Ваш код для получения credentials)

creds = credentials.Credentials.from_authorized_user_file('tokens/7597571554.pickle', SCOPES)
check_scopes(creds)
