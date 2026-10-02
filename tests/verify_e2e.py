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

print('[1] Testing Patient Registration...')
patient = post('/api/patients', {
    'name': 'Gita Devi',
    'age': 61,
    'gender': 'Female',
    'phone': '+91 91234 56789',
    'location': 'Primary Health Centre Ward 4',
    'occupation': 'Handloom Weaver',
    'activity_level': 'Moderate',
    'joint_injury': 1,
    'family_history': 1,
    'demanding_work': 1,
    'walking_difficulty': 2,
    'stair_difficulty': 3,
    'morning_stiffness': 2
})
print(f"Registered Patient: {patient['name']} (Code: {patient['patient_code']}, ID: {patient['id']})")

print('\n[2] Testing Screening Submission & ML Inference...')
screening = post('/api/screenings', {
    'patient_id': patient['id'],
    'questionnaire': {
        'knee_pain': 3,
        'joint_stiffness': 3,
        'walking_difficulty': 2,
        'stair_difficulty': 3,
        'standing_difficulty': 2,
        'knee_bending_difficulty': 3,
        'pain_increase_activity': 3,
        'pain_scale': 7.0,
        'mobility_scale': 4.0
    },
    'movement': {
        'left_knee_rom': 88.0,
        'right_knee_rom': 116.0,
        'knee_symmetry': 75.8,
        'average_knee_angle': 102.0,
        'gait_symmetry': 72.0,
        'movement_consistency': 74.0,
        'posture_score': 71.0,
        'hip_movement': 28.0,
        'ankle_movement': 20.0,
        'movement_smoothness': 68.0,
        'frames': [
            {'timestamp': 100.0, 'left_knee_angle': 90.0, 'right_knee_angle': 115.0},
            {'timestamp': 200.0, 'left_knee_angle': 88.0, 'right_knee_angle': 116.0}
        ]
    },
    'notes': 'Clinical screening test with high symptom burden'
})
print(f"Screening Result: {screening['risk_level']} (Probability: {screening['risk_probability']}%)")
print(f"Model Confidence: {screening['confidence']}% | Questionnaire: {screening['questionnaire_contribution']}% | Movement: {screening['movement_contribution']}%")

print('\n[3] Testing PDF Report Generation...')
report = post('/api/reports/generate', {'screening_id': screening['id']})
print(f"Report Generated: {report['file_name']} (Report ID: {report['report_id']})")

print('\n[4] Testing PDF Download...')
report_id = report['report_id']
with urllib.request.urlopen(f"{BASE}/api/reports/{report_id}") as resp:
    pdf_bytes = resp.read()
    print(f"Downloaded PDF: {len(pdf_bytes)} bytes. Content-Type: {resp.headers.get('Content-Type')}")
    assert len(pdf_bytes) > 1000
    assert 'application/pdf' in resp.headers.get('Content-Type')

print('\n>>> ALL 4 VERIFICATION STAGES COMPLETED WITH 100% SUCCESS! <<<')
