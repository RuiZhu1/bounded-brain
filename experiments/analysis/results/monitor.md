## Specs and bounds

| Suite | K_e (engage) | K_d (deadline) | Step limit |
|---|---|---|---|
| libero_10 | 197 (9.8 s) | 433 (21.6 s) | 520 (26 s) |
| libero_90 | 376 (18.8 s) | 400 (20.0 s) | 400 (20 s) |
| libero_goal | 257 (12.8 s) | 300 (15.0 s) | 300 (15 s) |
| libero_object | 153 (7.7 s) | 205 (10.2 s) | 280 (14 s) |
| libero_spatial | 129 (6.5 s) | 173 (8.7 s) | 280 (14 s) |

Monitor verdict = reference semantics on 16248/16248 (episode, spec) pairs. Largest monitor state (formula nodes): wrong_object 2, collateral 6, engage 4, deadline 2.

## Held-out episodes (calibration units excluded)

Failed episodes: share with a violation, median time of the verdict and median lead time before the step limit. Successful episodes: share with a violation before success.

| Spec | Group | Failures flagged | Verdict at (median) | Lead (median) | Episode left (median) | Successes flagged |
|---|---|---|---|---|---|---|
| wrong_object | reproduction | 0/20 (0%) | — | — | — | 1/780 (0.1%) |
| wrong_object | randinit | 6/32 (19%) | 10.3 s | 3.7 s | 26% | 0/1218 (0.0%) |
| wrong_object | ood90 | 442/941 (47%) | 3.2 s | 16.8 s | 84% | 130/397 (32.7%) |
| collateral | reproduction | 1/20 (5%) | 12.9 s | 2.1 s | 14% | 8/780 (1.0%) |
| collateral | randinit | 7/32 (22%) | 11.2 s | 4.0 s | 28% | 8/1218 (0.7%) |
| collateral | ood90 | 494/941 (52%) | 3.9 s | 16.1 s | 80% | 139/397 (35.0%) |
| engage | reproduction | 10/20 (50%) | 12.8 s | 2.1 s | 14% | 1/780 (0.1%) |
| engage | randinit | 15/32 (47%) | 7.7 s | 6.3 s | 45% | 0/1218 (0.0%) |
| engage | ood90 | 564/941 (60%) | 18.8 s | 1.2 s | 6% | 1/397 (0.3%) |
| deadline | reproduction | 20/20 (100%) | 15.0 s | 0.0 s | 0% | 6/780 (0.8%) |
| deadline | randinit | 32/32 (100%) | 12.6 s | 4.3 s | 22% | 7/1218 (0.6%) |
| deadline | ood90 | 941/941 (100%) | 20.0 s | 0.0 s | 0% | 0/397 (0.0%) |
| early (all but deadline) | reproduction | 10/20 (50%) | 12.8 s | 2.1 s | 14% | 9/780 (1.2%) |
| early (all but deadline) | randinit | 18/32 (56%) | 9.4 s | 6.3 s | 45% | 8/1218 (0.7%) |
| early (all but deadline) | ood90 | 670/941 (71%) | 4.5 s | 15.5 s | 77% | 139/397 (35.0%) |
| any | reproduction | 20/20 (100%) | 12.8 s | 2.1 s | 14% | 14/780 (1.8%) |
| any | randinit | 32/32 (100%) | 10.8 s | 4.3 s | 27% | 15/1218 (1.2%) |
| any | ood90 | 941/941 (100%) | 9.7 s | 10.3 s | 52% | 139/397 (35.0%) |
