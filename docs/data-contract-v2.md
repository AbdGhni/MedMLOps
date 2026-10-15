# Synthetic event v2 contract

All subjects and labels are artificial. Population realism, clinical validation and medical recommendations are expressly excluded.

| Feature | Simulated unit / meaning | Technical bound |
|---|---|---|
| age | fictitious age in years | 18–100 |
| sex_code | fictitious binary demographic code, no asserted clinical effect | 0 or 1 |
| creatinine | simulated laboratory numeric value, demo mg/dL scale | 0.3–4 |
| crp | simulated laboratory numeric value, demo mg/L scale | 0–150 |
| heart_rate | simulated beats/min | 40–180 |
| systolic_bp | simulated mmHg | 70–220 |
| oxygen_saturation | simulated percentage | 80–100 |
| temperature | simulated degrees Celsius | 35–42 |
| bmi | simulated BMI numeric scale | 15–50 |
| prior_event | fictitious event history | 0 or 1 |

The bounds and generator coefficients are technical exercise choices, not normal ranges, clinical criteria or population estimates. `synthetic_id` is an artificial unique split identifier, not a model feature. `target` is a Bernoulli sample of a fabricated logistic event and is never an input feature. There is one independent row per subject; no longitudinal joins.

Strict Pydantic inference schema refuses extra fields, strings masquerading as numbers, booleans and nonfinite values. Integer-coded features require actual integer values. Dataset gates also reject duplicates, missing values, unsupported columns, out-of-range features and degenerate labels. Class prevalence must lie between 5 % and 80 % as a demonstration quality constraint.

Snapshots contain a CSV and manifest. The version is the SHA-256 of canonical CSV bytes (fixed column order, twelve-significant-digit numeric serialization and LF endings). The loader verifies bytes before reading. Training uses the loaded snapshot values, not a separately regenerated in-memory cohort. Prepared arrays are hashed in their manifest and checked before fitting; train/validation/test subject IDs must be disjoint.

Data snapshots and fitted model artifacts are excluded from Git. DVC stage definitions exist; DVC initialization, cache/remote and actual reproduction are pending installation. Hashing files alone is not claimed as a DVC implementation.
