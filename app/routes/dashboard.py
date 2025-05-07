# app/routes/dashboard.py

from flask import Blueprint, redirect, url_for, render_template

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    return redirect(url_for('dashboard.dashboard'))

@dashboard_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/tview')
def tv_view():
    return render_template('tv_view.html')

@dashboard_bp.route('/keypad')
def keypad():
    return render_template('keypad.html')

@dashboard_bp.route('/keypad2')
def keypad2():
    return render_template('keypad2.html')
