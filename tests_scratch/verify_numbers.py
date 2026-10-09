import csv
import re

# Load CSV data
csv_lookup = {}
with open('results/phase8_2_statistical_comparison.csv', 'r') as f:
    for row in csv.DictReader(f):
        key = (row['scenario'], row['scale'])
        csv_lookup[key] = row

# Parse Synthesis V5 Section 6.1 Table
table_lines = r"""
| **S1: Honest Baseline** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S1: Honest Baseline** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S2: Closed Collusion** | Standard | $0.0850$ | $0.0889$ | $+0.0039$ | $+4.53\%$ | $+1.472$ | $0.158$ | $+0.33$ |
| **S2: Closed Collusion** | Extended | $0.0539$ | $0.0611$ | $+0.0073$ | $+13.50\%$ | $+3.944$ | $8.70 \times 10^{-4}$ | $+0.88$ |
| **S3: Leaky Collusion** | **Standard** | **$0.1834$** | **$0.1084$** | **$-0.0750$** | **$-40.88\%$** | **$-34.354$** | **$1.44 \times 10^{-18}$** | **$-7.68$** |
| **S3: Leaky Collusion** | **Extended** | **$0.1982$** | **$0.1160$** | **$-0.0823$** | **$-41.50\%$** | **$-50.410$** | **$1.07 \times 10^{-21}$** | **$-11.27$** |
| **S4: Connected ($p=0.00$)**| Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S4: Connected ($p=0.05$)**| Standard | $0.0935$ | $0.1176$ | $+0.0242$ | $+25.89\%$ | $+11.757$ | $3.66 \times 10^{-10}$ | $+2.63$ |
| **S4: Connected ($p=0.10$)**| Standard | $0.1606$ | $0.1885$ | $+0.0279$ | $+17.34\%$ | $+13.621$ | $2.96 \times 10^{-11}$ | $+3.05$ |
| **S4: Connected ($p=0.20$)**| Standard | $0.2731$ | $0.2920$ | $+0.0189$ | $+6.92\%$ | $+9.209$ | $1.95 \times 10^{-8}$ | $+2.06$ |
| **S4: Connected ($p=0.40$)**| Standard | $0.4124$ | $0.4045$ | $-0.0079$ | $-1.90\%$ | $-4.799$ | $1.25 \times 10^{-4}$ | $-1.07$ |
| **S5: Adaptive Attacker** | Standard | $0.0964$ | $0.1004$ | $+0.0040$ | $+4.16\%$ | $+1.739$ | $0.098$ | $+0.39$ |
| **S6: Receipt Grinding** | Standard | $0.0922$ | $0.1046$ | $+0.0123$ | $+13.38\%$ | $+3.860$ | $1.06 \times 10^{-3}$ | $+0.86$ |
| **S6: Receipt Grinding** | Extended | $0.0558$ | $0.0658$ | $+0.0100$ | $+17.92\%$ | $+4.968$ | $8.55 \times 10^{-5}$ | $+1.11$ |
| **S7: Dispute Manip** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S8: Asym Uploader** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S8: Asym Uploader** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S9: Reciprocal Comm** | Standard | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
| **S9: Reciprocal Comm** | Extended | $0.0000$ | $0.0000$ | $0.0000$ | $0.00\%$ | $0.00$ | $1.000$ | $0.00$ |
"""

name_map = {
    'S1: Honest Baseline': 'scenario_1_honest_baseline',
    'S2: Closed Collusion': 'scenario_2_closed_collusion',
    'S3: Leaky Collusion': 'scenario_3_leaky_collusion',
    'S4: Connected ($p=0.00$)': 'scenario_4_bridge_00',
    'S4: Connected ($p=0.05$)': 'scenario_4_bridge_05',
    'S4: Connected ($p=0.10$)': 'scenario_4_bridge_10',
    'S4: Connected ($p=0.20$)': 'scenario_4_bridge_20',
    'S4: Connected ($p=0.40$)': 'scenario_4_bridge_40',
    'S5: Adaptive Attacker': 'scenario_5_adaptive_attacker',
    'S6: Receipt Grinding': 'scenario_6_receipt_grinding',
    'S7: Dispute Manip': 'scenario_7_dispute_manipulation',
    'S8: Asym Uploader': 'scenario_8_honest_asymmetric_uploader',
    'S9: Reciprocal Comm': 'scenario_9_honest_reciprocal_community'
}

print("Running mechanical check against results/phase8_2_statistical_comparison.csv...\n")
mismatches = 0
checks = 0

for line in table_lines.strip().split('\n'):
    parts = [p.strip() for p in line.split('|')[1:-1]]
    if not parts or len(parts) < 9:
        continue
    scen_raw = parts[0].replace('**', '')
    scale_raw = parts[1].replace('**', '').lower()
    scen_key = name_map.get(scen_raw)
    if not scen_key:
        print(f"ERROR: Cannot map scenario '{scen_raw}'")
        mismatches += 1
        continue
    
    csv_row = csv_lookup.get((scen_key, scale_raw))
    if not csv_row:
        print(f"ERROR: No CSV row for ({scen_key}, {scale_raw})")
        mismatches += 1
        continue

    def clean_num(s):
        s = s.replace('**', '').replace('$', '').replace('+', '').strip()
        m = re.search(r'([0-9.]+)\s*\\times\s*10\^\{?(-?[0-9]+)\}?', s)
        if m:
            return float(m.group(1)) * (10 ** int(m.group(2)))
        s = s.replace(r'\%', '').replace('%', '').replace('\\', '').strip()
        return float(s)

    v_mean = clean_num(parts[2])
    ew_mean = clean_num(parts[3])
    diff = clean_num(parts[4])
    rel = clean_num(parts[5])
    t_stat = clean_num(parts[6])
    p_val = clean_num(parts[7])
    dz = clean_num(parts[8])

    csv_v = float(csv_row['vanilla_colluder_mean'])
    csv_ew = float(csv_row['ew_colluder_mean'])
    csv_diff = float(csv_row['absolute_difference'])
    csv_rel = float(csv_row['relative_difference_pct'])
    csv_t = float(csv_row['paired_t_statistic'])
    csv_p = float(csv_row['p_value'])
    csv_dz = float(csv_row['cohens_dz'])

    # Comparisons with appropriate rounding tolerances
    def check_val(name, doc_val, csv_val, tol):
        global checks, mismatches
        checks += 1
        if abs(doc_val - csv_val) > tol:
            print(f"MISMATCH in {scen_raw} ({scale_raw}) for {name}: doc={doc_val}, csv={csv_val}")
            mismatches += 1

    check_val("vanilla_colluder_mean", v_mean, csv_v, 0.0005)
    check_val("ew_colluder_mean", ew_mean, csv_ew, 0.0005)
    check_val("absolute_difference", diff, csv_diff, 0.0005)
    check_val("relative_difference_pct", rel, csv_rel, 0.05)
    check_val("paired_t_statistic", t_stat, csv_t, 0.005)
    # For p-value, relative tolerance if small, absolute if large
    checks += 1
    if csv_p > 0.01:
        if abs(p_val - csv_p) > 0.005:
            print(f"MISMATCH in {scen_raw} ({scale_raw}) for p-value: doc={p_val}, csv={csv_p}")
            mismatches += 1
    else:
        if abs(p_val - csv_p) / (csv_p + 1e-30) > 0.05:
            print(f"MISMATCH in {scen_raw} ({scale_raw}) for p-value: doc={p_val}, csv={csv_p}")
            mismatches += 1
    check_val("cohens_dz", dz, csv_dz, 0.01)

print(f"Mechanical check complete: {checks} checks executed. Mismatches found: {mismatches}")
