import urllib.request
import json

BASE = 'http://127.0.0.1:8000'

def post(endpoint, data):
    req = urllib.request.Request(
        f'{BASE}{endpoint}',
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get(endpoint):
    with urllib.request.urlopen(f'{BASE}{endpoint}') as resp:
        return json.loads(resp.read().decode('utf-8'))

def test_workflow():
    print('[Step 1] Registering Patient A (Alpha)...')
    p_a = post('/api/patients', {
        'name': 'Patient Alpha',
        'age': 58,
        'gender': 'Female',
        'phone': '+91 98765 43210',
        'location': 'Ward 1',
        'occupation': 'Teacher',
        'activity_level': 'Moderate'
    })
    print(f"Registered Patient A: {p_a['name']} (ID: {p_a['id']}, Code: {p_a['patient_code']})")

    print('\n[Step 2] Completing Screening for Patient A...')
    screen_a = post('/api/screenings', {
        'patient_id': p_a['id'],
        'questionnaire': {
            'knee_pain': 3,
            'joint_stiffness': 3,
            'walking_difficulty': 2,
            'stair_difficulty': 3,
            'standing_difficulty': 2,
            'knee_bending_difficulty': 3,
            'pain_increase_activity': 3,
            'pain_scale': 8.0,
            'mobility_scale': 3.0
        },
        'movement': {
            'left_knee_rom': 85.0,
            'right_knee_rom': 110.0,
            'knee_symmetry': 72.0,
            'average_knee_angle': 98.0,
            'gait_symmetry': 70.0,
            'movement_consistency': 68.0,
            'posture_score': 65.0,
            'hip_movement': 25.0,
            'ankle_movement': 18.0,
            'movement_smoothness': 65.0,
            'assessment_status': 'VALID',
            'landmark_quality_score': 95.0,
            'valid_frame_ratio': 1.0,
            'movement_quality_score': 85.0,
            'frames': [
                {'timestamp': 0.1, 'left_knee_angle': 90.0, 'right_knee_angle': 110.0, 'frame_valid': True},
                {'timestamp': 0.2, 'left_knee_angle': 85.0, 'right_knee_angle': 112.0, 'frame_valid': True}
            ]
        },
        'notes': 'Patient A screening notes'
    })
    print(f"Completed Screening A: ID={screen_a['id']}, Risk={screen_a['risk_level']}, Prob={screen_a['risk_probability']}%")

    print('\n[Step 3] Registering Patient B (Beta) fresh...')
    p_b = post('/api/patients', {
        'name': 'Patient Beta',
        'age': 34,
        'gender': 'Male',
        'phone': '+91 91234 56789',
        'location': 'Ward 2',
        'occupation': 'Software Engineer',
        'activity_level': 'High'
    })
    print(f"Registered Patient B: {p_b['name']} (ID: {p_b['id']}, Code: {p_b['patient_code']})")

    print('\n[Step 4] Completing Screening for Patient B...')
    screen_b = post('/api/screenings', {
        'patient_id': p_b['id'],
        'questionnaire': {
            'knee_pain': 0,
            'joint_stiffness': 0,
            'walking_difficulty': 0,
            'stair_difficulty': 0,
            'standing_difficulty': 0,
            'knee_bending_difficulty': 0,
            'pain_increase_activity': 0,
            'pain_scale': 0.0,
            'mobility_scale': 9.0
        },
        'movement': {
            'left_knee_rom': 135.0,
            'right_knee_rom': 136.0,
            'knee_symmetry': 98.0,
            'average_knee_angle': 135.0,
            'gait_symmetry': 95.0,
            'movement_consistency': 96.0,
            'posture_score': 92.0,
            'hip_movement': 35.0,
            'ankle_movement': 28.0,
            'movement_smoothness': 94.0,
            'assessment_status': 'VALID',
            'landmark_quality_score': 98.0,
            'valid_frame_ratio': 1.0,
            'movement_quality_score': 95.0,
            'frames': [
                {'timestamp': 0.1, 'left_knee_angle': 135.0, 'right_knee_angle': 136.0, 'frame_valid': True},
                {'timestamp': 0.2, 'left_knee_angle': 134.0, 'right_knee_angle': 135.0, 'frame_valid': True}
            ]
        },
        'notes': 'Patient B screening notes'
    })
    print(f"Completed Screening B: ID={screen_b['id']}, Risk={screen_b['risk_level']}, Prob={screen_b['risk_probability']}%")

    print('\n[Step 5] Verifying Patient A record preservation and isolation...')
    screenings_a = get(f"/api/screenings?patient_id={p_a['id']}")
    print(f"Patient A has {len(screenings_a)} screenings in DB.")
    assert len(screenings_a) >= 1
    assert screenings_a[0]['id'] == screen_a['id']
    assert screenings_a[0]['patient_id'] == p_a['id']
    assert screenings_a[0]['id'] != screen_b['id']

    # Also check /api/patients/{id} history endpoint
    detail_a = get(f"/api/patients/{p_a['id']}")
    print(f"Patient A detail endpoint reports {len(detail_a['screenings'])} screenings in history.")
    assert len(detail_a['screenings']) >= 1
    assert detail_a['screenings'][0]['id'] == screen_a['id']

    print('\n[Step 6] Verifying Patient B record isolation...')
    screenings_b = get(f"/api/screenings?patient_id={p_b['id']}")
    print(f"Patient B has {len(screenings_b)} screenings in DB.")
    assert len(screenings_b) >= 1
    assert screenings_b[0]['id'] == screen_b['id']
    assert screenings_b[0]['patient_id'] == p_b['id']

    print('\n[Step 7] Generating and downloading PDF for Patient A...')
    rep_a = post('/api/reports/generate', {'screening_id': screen_a['id']})
    print(f"Patient A PDF Report ID: {rep_a['report_id']}, File: {rep_a['file_name']}")
    with urllib.request.urlopen(f"{BASE}/api/reports/{rep_a['report_id']}") as resp:
        pdf_bytes = resp.read()
        assert len(pdf_bytes) > 1000
        print(f"Patient A PDF verified: {len(pdf_bytes)} bytes.")

    print('\n[Step 8] Verifying distinct Patient Directory entries...')
    all_patients = get('/api/patients')
    patient_ids = [p['id'] for p in all_patients]
    assert p_a['id'] in patient_ids
    assert p_b['id'] in patient_ids

    print('\n>>> DUAL-PATIENT ISOLATION & HISTORY PRESERVATION CONFIRMED 100%! <<<')

if __name__ == '__main__':
    test_workflow()
