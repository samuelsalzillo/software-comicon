from flask import Blueprint, render_template

provaE = Blueprint('provaE',__name__)


@provaE.route('/provaE1')
def provaE1():
    return render_template('provaE1.html')

@provaE.route('/provaE2')
def provaE2():
    return render_template('provaE2.html')
