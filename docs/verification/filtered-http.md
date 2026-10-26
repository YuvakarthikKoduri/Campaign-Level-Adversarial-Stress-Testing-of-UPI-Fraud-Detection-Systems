# Research snapshot: pilot-main

Generated UTC: 2026-10-26T03:12:44.043539+00:00

Filters: {"detector": "xgboost", "strategy": "rule", "family": "gradual_escalation", "block": "", "outcome": ""}

This is a synthetic research environment. Results do not establish real-world UPI fraud-detection effectiveness.

Gross transfer is simulated source debit, not actual victim loss.

Imported software verification is not scientific validation.

```csv
detector,family,strategy,campaigns,completed,completion,blocks,block_sd,allow,flag,block,mean_attempts,gross
xgboost,gradual_escalation,rule,360,271,75.27777777777777,9,14.331152934933197,1561,11,89,4.613888888888889,10281177.819999995

```

## Benign controls
[
  {
    "detector": "xgboost",
    "stratum": "benign_mimic_test",
    "rate": 48.27777777777778,
    "n": 3600,
    "blocked": 1738,
    "alerted": 1862,
    "sources": [
      {
        "id": "aebf23ae03c2db2c4dc9aea5",
        "name": "benign_scores.json",
        "bytes": 257305,
        "url": "/api/files/aebf23ae03c2db2c4dc9aea5"
      },
      {
        "id": "59a3065442ebc5249de73638",
        "name": "benign_scores.json",
        "bytes": 255625,
        "url": "/api/files/59a3065442ebc5249de73638"
      },
      {
        "id": "d4a2a02c20ea423f3153de7e",
        "name": "benign_scores.json",
        "bytes": 257259,
        "url": "/api/files/d4a2a02c20ea423f3153de7e"
      },
      {
        "id": "b9056962b3877482f8940f47",
        "name": "benign_scores.json",
        "bytes": 257908,
        "url": "/api/files/b9056962b3877482f8940f47"
      },
      {
        "id": "861765fc589a63d646d480e2",
        "name": "benign_scores.json",
        "bytes": 256606,
        "url": "/api/files/861765fc589a63d646d480e2"
      },
      {
        "id": "ad398923e8c546ae24edf3dd",
        "name": "benign_scores.json",
        "bytes": 256735,
        "url": "/api/files/ad398923e8c546ae24edf3dd"
      },
      {
        "id": "0711edb1153f76b6e7424f98",
        "name": "benign_scores.json",
        "bytes": 257616,
        "url": "/api/files/0711edb1153f76b6e7424f98"
      },
      {
        "id": "4c2df7d0ca18bae95e661fc8",
        "name": "benign_scores.json",
        "bytes": 258535,
        "url": "/api/files/4c2df7d0ca18bae95e661fc8"
      },
      {
        "id": "12627897ba4cc72ce5d65fda",
        "name": "benign_scores.json",
        "bytes": 256462,
        "url": "/api/files/12627897ba4cc72ce5d65fda"
      }
    ]
  },
  {
    "detector": "xgboost",
    "stratum": "benign_test",
    "rate": 0.0,
    "n": 3600,
    "blocked": 0,
    "alerted": 56,
    "sources": [
      {
        "id": "aebf23ae03c2db2c4dc9aea5",
        "name": "benign_scores.json",
        "bytes": 257305,
        "url": "/api/files/aebf23ae03c2db2c4dc9aea5"
      },
      {
        "id": "59a3065442ebc5249de73638",
        "name": "benign_scores.json",
        "bytes": 255625,
        "url": "/api/files/59a3065442ebc5249de73638"
      },
      {
        "id": "d4a2a02c20ea423f3153de7e",
        "name": "benign_scores.json",
        "bytes": 257259,
        "url": "/api/files/d4a2a02c20ea423f3153de7e"
      },
      {
        "id": "b9056962b3877482f8940f47",
        "name": "benign_scores.json",
        "bytes": 257908,
        "url": "/api/files/b9056962b3877482f8940f47"
      },
      {
        "id": "861765fc589a63d646d480e2",
        "name": "benign_scores.json",
        "bytes": 256606,
        "url": "/api/files/861765fc589a63d646d480e2"
      },
      {
        "id": "ad398923e8c546ae24edf3dd",
        "name": "benign_scores.json",
        "bytes": 256735,
        "url": "/api/files/ad398923e8c546ae24edf3dd"
      },
      {
        "id": "0711edb1153f76b6e7424f98",
        "name": "benign_scores.json",
        "bytes": 257616,
        "url": "/api/files/0711edb1153f76b6e7424f98"
      },
      {
        "id": "4c2df7d0ca18bae95e661fc8",
        "name": "benign_scores.json",
        "bytes": 258535,
        "url": "/api/files/4c2df7d0ca18bae95e661fc8"
      },
      {
        "id": "12627897ba4cc72ce5d65fda",
        "name": "benign_scores.json",
        "bytes": 256462,
        "url": "/api/files/12627897ba4cc72ce5d65fda"
      }
    ]
  }
]

## Evidence
[
  {
    "id": "9ff58b915d11f3f83aa681bb",
    "name": "manifest.json",
    "bytes": 16778,
    "url": "/api/files/9ff58b915d11f3f83aa681bb"
  }
]

Gate C: HOLD