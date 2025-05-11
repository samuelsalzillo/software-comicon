from flask import Blueprint, render_template

controls = Blueprint('controls',__name__,url_prefix='/controls')

# Aggiungi queste route
@controls.route('/statico')
def controls_statico():
    return render_template('controls_statico.html')

@controls.route('/combined')
def controls_combined():
    return render_template('controls_combined1.html')

@controls.route('/combined2')
def controls_combined2():
    return render_template('controls_combined2.html')


@controls.route('/cassa')
def controls_cassa():
    return render_template('controls_cassa.html')


@controls.route('/couple')
def controls_couple():
    return render_template('controls_couple.html')


@controls.route('/single')
def controls_single():
    return render_template('controls_single.html')


@controls.route('/charlie')
def controls_charlie():
    return render_template('controls_charlie.html')