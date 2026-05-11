import json

with open('fairxai_synthetic_resumes_600_imbalanced.json', 'r') as f:
    json_data = json.load(f)

data = json_data['resumes']

# Analyze by experience level
entry = [r for r in data if r.get('experience_level') == 'entry']
mid = [r for r in data if r.get('experience_level') == 'mid']
senior = [r for r in data if r.get('experience_level') == 'senior']

print('Experience Level Distribution:')
print(f'Entry (0-2y): {len(entry)} resumes')
entry_strong = sum(1 for r in entry if r.get('is_strong', False))
entry_weak = len(entry) - entry_strong
print(f'  Strong: {entry_strong} ({100*entry_strong/len(entry):.1f}%)')
print(f'  Weak: {entry_weak} ({100*entry_weak/len(entry):.1f}%)')
print()

print(f'Mid (3-7y): {len(mid)} resumes')
mid_strong = sum(1 for r in mid if r.get('is_strong', False))
mid_weak = len(mid) - mid_strong
print(f'  Strong: {mid_strong} ({100*mid_strong/len(mid):.1f}%)')
print(f'  Weak: {mid_weak} ({100*mid_weak/len(mid):.1f}%)')
print()

print(f'Senior (8+y): {len(senior)} resumes')
senior_strong = sum(1 for r in senior if r.get('is_strong', False))
senior_weak = len(senior) - senior_strong
print(f'  Strong: {senior_strong} ({100*senior_strong/len(senior):.1f}%)')
print(f'  Weak: {senior_weak} ({100*senior_weak/len(senior):.1f}%)')
print()

print('Chart Data Values:')
print(f'Experience Level Imbalance Chart (Strong): [{entry_strong}, {mid_strong}, {senior_strong}]')
print(f'Experience Level Imbalance Chart (Weak): [{entry_weak}, {mid_weak}, {senior_weak}]')
print(f'Strong Percentage Chart: [{100*entry_strong/len(entry):.0f}, {100*mid_strong/len(mid):.0f}, {100*senior_strong/len(senior):.0f}]')
if mid_strong > 0:
    print(f'Imbalance Ratio: Mid={mid_weak/mid_strong:.2f}, Senior={senior_weak/senior_strong:.2f}')
