# Evaluation strategy

Before selecting models or setting indicator thresholds:

1. Obtain institution approval and define lawful purpose, consent/notice, retention, access controls, and an approved data handling plan.
2. Create a small representative, de-identified validation set spanning camera angles, lighting, distance, occlusion, room occupancy, and recording quality; separate development and holdout segments by lecture to avoid leakage.
3. Have qualified human annotators label only observable quantities (person/face visibility, approximate head orientation, eye state) under a written rubric; measure annotator agreement and mark ambiguous cases unknown.
4. Evaluate detector precision/recall, tracking association quality, landmark/head/eye error where labels support it, calibration, failure rate, processing throughput, and coverage. Stratify results across recording conditions; do not treat aggregate accuracy as proof of fairness or suitability.
5. Validate temporal feature behavior and analytics formulas on hand-checked examples; test low coverage, missingness, and confounders. No user-facing indicator until thresholds and minimum coverage rules are approved.
6. Version dataset manifests, annotation rubric, model/config, code, and metrics. Restrict access; do not commit videos or identifiable frames.

Known limitations include occlusion, camera placement/angle, lighting, eyewear, seating distance, head pose ambiguity, frame sampling aliasing, codec artifacts, and inability to infer gaze/attention reliably from all views. Visual proxies do not establish attention, drowsiness, distraction, engagement, or psychological state. Reports must communicate this distinction.
