# app/routes/controls.py

from flask import Blueprint, render_template

controls_bp = Blueprint('controls', __name__)

@controls_bp.route('/controls/statico')
def controls_statico():
    return render_template('controls_statico.html')

@controls_bp.route('/controls/combined')
def controls_combined():
    return render_template('controls_combined1.html')

@controls_bp.route('/controls/combined2')
def controls_combined2():
    return render_template('controls_combined2.html')

@controls_bp.route('/controls/cassa')
def controls_cassa():
    return render_template('controls_cassa.html')

@controls_bp.route('/controls/couple')
def controls_couple():
    return render_template('controls_couple.html')

@controls_bp.route('/controls/single')
def controls_single():
    return render_template('controls_single.html')

@controls_bp.route('/controls/charlie')
def controls_charlie():
    return render_template('controls_charlie.html')
