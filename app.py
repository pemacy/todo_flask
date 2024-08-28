# pylint: disable=import-error, use-dict-literal, unused-argument

import os
import secrets
from functools import wraps
from flask import (
    Flask,
    render_template,
    url_for,
    redirect,
    session,
    request,
    flash,
    g,
)
from werkzeug.exceptions import NotFound
from todos.database_persistence import DatabasePersistence
from todos.utils import (
    error_for_list_title,
    error_for_todo,
    todos_remaining,
    is_list_completed,
    sort_items,
    is_todo_completed,
)

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

def require_list(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        list_id = kwargs.get('list_id')
        lst = g.db.find_list(list_id)
        if not lst:
            raise NotFound(description="List not found")
        return f(lst=lst, *args, **kwargs)

    return decorated_function

def require_todo(f):
    @wraps(f)
    @require_list
    def decorated_function(lst, *args, **kwargs):
        todo_id = kwargs.get('todo_id')
        todo = g.db.find_todo(todo_id)
        if not todo:
            raise NotFound(description="Todo not found")
        return f(lst=lst, todo=todo, *args, **kwargs)

    return decorated_function

@app.context_processor
def list_utilities_processor():
    return dict(
                is_list_completed=is_list_completed,
            )

@app.before_request
def connect_db():
    g.db = DatabasePersistence(session)

@app.route("/")
def index():
    return redirect(url_for('get_lists'))

@app.route("/lists", methods=["GET"])
def get_lists():
    lists = sort_items(g.db.all_lists(), is_list_completed)
    return render_template('lists.html',
                           lists=lists,
                           todos_remaining=todos_remaining)

@app.route("/lists", methods=["POST"])
def create_list():
    title = request.form["list_title"].strip()
    error = error_for_list_title(title, g.db.all_lists())
    if error:
        flash(error, "error")
        return render_template('new_list.html', title=title)

    g.db.create_new_list(title)
    flash("The list has been created.", "success")
    return redirect(url_for('get_lists'))

@app.route("/lists/new")
def add_todo():
    return render_template('new_list.html')

@app.route("/lists/<int:list_id>")
@require_list
def show_list(lst, list_id):
    todos = sort_items(lst['todos'], is_todo_completed)
    return render_template('list.html', lst=lst, todos=todos)

@app.route("/lists/<int:list_id>/todos", methods=["POST"])
#highlight
@require_list
def create_todo(lst, list_id):
    todo_title = request.form["todo"].strip()

#endhighlight
    error = error_for_todo(todo_title)
    if error:
        flash(error, "error")
        return render_template('list.html', lst=lst, todo_title=todo_title)

    g.db.create_new_todo(list_id, todo_title)
    flash("The todo was added.", "success")
    return redirect(url_for('show_list', list_id=list_id))

@app.route("/lists/<int:list_id>/todos/<int:todo_id>/toggle", methods=["POST"])
#highlight
@require_todo
def update_todo_status(lst, todo, list_id, todo_id):
    status = request.form['completed']
    g.db.update_todo_status(todo_id, status)
#endhighlight
    flash("The todo has been updated.", "success")
    return redirect(url_for('show_list', list_id=list_id))

@app.route("/lists/<int:list_id>/todos/<int:todo_id>/delete", methods=["POST"])
#highlight
@require_todo
def delete_todo(lst, todo, list_id, todo_id):
    g.db.delete_todo_from_list(todo_id)
#endhighlight
    flash("The todo has been deleted.", "success")
    return redirect(url_for('show_list', list_id=list_id))

@app.route("/lists/<int:list_id>/complete_all", methods=["POST"])
#highlight
@require_list
def mark_all_todos_completed(lst, list_id):
    g.db.mark_all_todos_completed(list_id)
#endhighlight
    flash("All todos have been updated.", "success")
    return redirect(url_for('show_list', list_id=list_id))

@app.route("/lists/<int:list_id>/edit")
#highlight
@require_list
def edit_list(lst, list_id):
    return render_template('edit_list.html', lst=lst)
#endhighlight

@app.route("/lists/<int:list_id>/delete", methods=["POST"])
#highlight
@require_list
def delete_list(lst, list_id):
#endhighlight
    g.db.delete_list(list_id)
    flash("The list has been deleted.", "success")
    return redirect(url_for('get_lists'))

@app.route("/lists/<int:list_id>", methods=["POST"])
#highlight
@require_list
def update_list(lst, list_id):
    title = request.form["list_title"].strip()
#endhighlight
    error = error_for_list_title(title, g.db.all_lists())
    if error:
        flash(error, "error")
        return render_template('edit_list.html', lst=lst, title=title)

    g.db.update_list_name(list_id, title)
    flash("The list has been updated.", "success")
    return redirect(url_for('get_lists'))

if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)
