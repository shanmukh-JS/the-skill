import os
from app import create_app, db
from app.models import User, Skill, LearningInterest, Request, Chat, Message, Rating, LearningHistory, Notification, FailedLogin

app = create_app(os.environ.get('FLASK_CONFIG', 'default'))

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Skill': Skill,
        'LearningInterest': LearningInterest,
        'Request': Request,
        'Chat': Chat,
        'Message': Message,
        'Rating': Rating,
        'LearningHistory': LearningHistory,
        'Notification': Notification,
        'FailedLogin': FailedLogin
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
