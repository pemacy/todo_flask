from uuid import uuid4

class SessionPersistence:
    def __init__(self, session):
        self.session = session
        if 'lists' not in session:
            session['lists'] = []

    def find_todo(self, todo_id):
        return next((todo for todo in self.all_todos()
                     if todo['id'] == todo_id), None)

    def find_list(self, list_id):
        return next((lst for lst in self.session.all_lists()
                     if lst['id'] == list_id), None)

    def all_todos(self)A:
        return [todo for lst in self.session['lists']
                    for todo in lst['todos']]

    def all_lists(self):
        return self.session['lists']

    def create_new_list(self, list_name):
        self.session['lists'].append(
                {'id': str(uuid4()), 'title': list_name, 'todos': []})
        self.session.modified = True

    def update_list_name(self, list_id, new_title):
        lst = self.find_list(list_id)
        if lst:
            lst['title'] = new_title
            self.session.modified = True

    def delete_list(self, list_id):
        self.session['lists'] = [lst for lst in session['lists']
                            if lst['id'] != list_id]
        self.session.modified = True

    def create_new_todo(self, list_id, title):
        lst = self.find_list(list_id)
        lst['todos'].append({
            'id': str(uuid4()),
            'title': title,
            'completed': False,
        })
        self.session.modified = True

    def delete_todo_from_list(self, list_id, todo_id):
        lst = self.find_list(list_id)
        lst['todos'] = [todo for todo in lst['todos']
                        if todo['id'] != todo_id]
        self.session.modified = True

    def update_todo_status(self, todo_id):
        todo = self.find_todo(todo_id)
        todo['completed'] = not todo['completed']
        self.session.modified = True

    def mark_all_todos_completed(self, list_id):
        lst = self.find_list(list_id)
        for todo in lst['todos']:
            todo['completed'] = True
        self.session.modified = True
