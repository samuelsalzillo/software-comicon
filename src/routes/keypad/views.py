from flask import Blueprint, render_template

keypad = Blueprint('keypad',__name__,url_prefix='')

@keypad.route('/keypad')
def get_keypad():
    return render_template('keypad.html')

@keypad.route('/keypad2')
def get_keypad2():
    return render_template('keypad2.html')