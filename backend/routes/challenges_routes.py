from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from models.challenges import (
    get_all_challenges,
    get_challenge_stats,
    get_plans_for_challenge,
    create_challenge,
    create_challenge_plan,
)

challenges_bp = Blueprint('challenges', __name__)


# ── List ──────────────────────────────────────────────────────────────────────

@challenges_bp.route('/challenges')
def challenges():
    return render_template(
        'challenges/challenges.html',
        challenges=get_all_challenges(),
        stats=get_challenge_stats(),
        active_page='challenges'
    )


# ── New challenge page ────────────────────────────────────────────────────────

@challenges_bp.route('/challenges/new', methods=['GET', 'POST'])
def challenge_new():
    if request.method == 'GET':
        return render_template(
            'challenges/challenge_new.html',
            active_page='challenges'
        )

    name      = request.form.get('challengeName', '').strip()
    is_active = int(request.form.get('isActive', 1))
    user_id   = session.get('user_id')

    if not name:
        flash('Challenge name is required.', 'error')
        return redirect(url_for('challenges.challenge_new'))

    try:
        create_challenge(name, is_active, user_id)
        flash('Challenge created successfully.', 'success')
        return redirect(url_for('challenges.challenges'))
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('challenges.challenge_new'))


# ── AJAX: get plans for a challenge ──────────────────────────────────────────

@challenges_bp.route('/challenges/<int:challenge_id>/plans', methods=['GET'])
def challenge_plans(challenge_id):
    try:
        plans = get_plans_for_challenge(challenge_id)
        return jsonify(plans)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── AJAX: add a plan to a challenge ─────────────────────────────────────────

@challenges_bp.route('/challenges/<int:challenge_id>/plans', methods=['POST'])
def challenge_plan_add(challenge_id):
    data    = request.get_json()
    plan    = (data.get('planName') or '').strip()
    user_id = session.get('user_id')

    if not plan:
        return jsonify({'success': False, 'error': 'Plan text is required.'}), 400

    try:
        create_challenge_plan(challenge_id, plan, user_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500