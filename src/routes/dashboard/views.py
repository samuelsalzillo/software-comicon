from flask import Blueprint, redirect, url_for, render_template

dashboard = Blueprint('dashboard',__name__,url_prefix='')

@dashboard.route('/')
def index():
    return redirect(url_for('dashboard.view_dashboard'))

@dashboard.route('/dashboard')
def view_dashboard():
    return render_template('dashboard.html')

@dashboard.route('/queue')
def queue():
    return render_template('queue.html')


@dashboard.route('/tview')
def tv_view():
    return render_template('tv_view.html')
