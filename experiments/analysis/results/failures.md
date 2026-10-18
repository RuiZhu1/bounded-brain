## Failure categories

| Category | reproduction | randinit | ood90 |
|---|---|---|---|
| never_touched | 7 (23%) | 4 (12%) | 66 (6%) |
| touched_no_grasp | 3 (10%) | 7 (22%) | 119 (11%) |
| wrong_object | 0 (0%) | 4 (12%) | 408 (36%) |
| mover_not_placed | 7 (23%) | 14 (44%) | 369 (33%) |
| no_progress | 3 (10%) | 0 (0%) | 126 (11%) |
| partial_goal | 11 (35%) | 3 (9%) | 40 (4%) |
| **failures / episodes** | 31 / 1200 | 32 / 1250 | 1128 / 1608 |

## LIBERO-90 (unseen tasks): success by scene family

| Scene family | Success |
|---|---|
| KITCHEN | 203/828 (25%) |
| LIVING_ROOM | 263/486 (54%) |
| STUDY | 14/294 (5%) |

## LIBERO-90 episodes that grasped an object the task does not move

| Outcome | Wrong grasps explained by the same scene's LIBERO-10 task | Other objects | Scene not in LIBERO-10 |
|---|---|---|---|
| failure | 238 | 12 | 287 |
| success | 128 | 0 | 29 |

In 532 of these 537 failed episodes the first grasp of the episode was already a wrong one.

Examples (instruction → objects grasped instead; the LIBERO-10 task(s) of that scene):

* "put the frying pan on the stove" → moka_pot_1; trained: "turn on the stove and put the moka pot on it"
* "turn on the stove and put the frying pan on it" → moka_pot_1; trained: "turn on the stove and put the moka pot on it"
* "close the bottom drawer of the cabinet" → akita_black_bowl_1; trained: "put the black bowl in the bottom drawer of the cabinet and close it"
* "close the bottom drawer of the cabinet and open the top drawer" → akita_black_bowl_1; trained: "put the black bowl in the bottom drawer of the cabinet and close it"
* "put the wine bottle in the bottom drawer of the cabinet" → akita_black_bowl_1; trained: "put the black bowl in the bottom drawer of the cabinet and close it"
* "put the wine bottle on the wine rack" → akita_black_bowl_1; trained: "put the black bowl in the bottom drawer of the cabinet and close it"
* "close the microwave" → white_yellow_mug_1; trained: "put the yellow and white mug in the microwave and close it"
* "put the right moka pot on the stove" → moka_pot_2; trained: "put both moka pots on the stove"
* "turn off the stove" → moka_pot_1, moka_pot_2; trained: "put both moka pots on the stove"
* "pick up the cream cheese box and put it in the basket" → alphabet_soup_1; trained: "put both the alphabet soup and the cream cheese box in the basket"
* "pick up the ketchup and put it in the basket" → alphabet_soup_1; trained: "put both the alphabet soup and the cream cheese box in the basket"
* "pick up the tomato sauce and put it in the basket" → alphabet_soup_1, cream_cheese_1; trained: "put both the alphabet soup and the cream cheese box in the basket"

## LIBERO-90 tasks never solved (all episodes failed)

| Instruction | Episodes | Main category |
|---|---|---|
| pick up the book and place it in the front compartment of the caddy | 54 | mover_not_placed |
| pick up the book and place it in the right compartment of the caddy | 54 | mover_not_placed |
| open the top drawer of the cabinet | 36 | no_progress |
| turn on the stove and put the frying pan on it | 36 | never_touched |
| close the bottom drawer of the cabinet and open the top drawer | 18 | partial_goal |
| close the top drawer of the cabinet and put the black bowl on top of it | 18 | mover_not_placed |
| open the bottom drawer of the cabinet | 18 | no_progress |
| open the microwave | 18 | no_progress |
| pick up the ketchup and put it in the basket | 18 | wrong_object |
| pick up the ketchup and put it in the tray | 18 | wrong_object |
| pick up the milk and put it in the basket | 18 | wrong_object |
| pick up the orange juice and put it in the basket | 18 | wrong_object |
| pick up the red mug and place it to the right of the caddy | 18 | wrong_object |
| pick up the salad dressing and put it in the tray | 18 | wrong_object |
| pick up the white mug and place it to the right of the caddy | 18 | mover_not_placed |
| pick up the yellow and white mug and place it to the right of the caddy | 18 | mover_not_placed |
| put the butter at the back in the top drawer of the cabinet and close it | 18 | wrong_object |
| put the butter at the front in the top drawer of the cabinet and close it | 18 | wrong_object |
| put the chocolate pudding in the top drawer of the cabinet and close it | 18 | wrong_object |
| put the chocolate pudding to the left of the plate | 18 | mover_not_placed |
| put the frying pan on the cabinet shelf | 18 | never_touched |
| put the frying pan on the stove | 18 | wrong_object |
| put the frying pan on top of the cabinet | 18 | never_touched |
| put the frying pan under the cabinet shelf | 18 | never_touched |
| put the ketchup in the top drawer of the cabinet | 18 | mover_not_placed |
| put the red mug on the left plate | 18 | wrong_object |
| put the red mug on the plate | 18 | wrong_object |
| put the red mug on the right plate | 18 | wrong_object |
| put the white bowl on top of the cabinet | 18 | touched_no_grasp |
| put the white bowl to the right of the plate | 18 | touched_no_grasp |
| put the wine bottle on the wine rack | 18 | touched_no_grasp |
| put the yellow and white mug to the front of the white mug | 18 | mover_not_placed |
| stack the black bowl at the front on the black bowl in the middle | 18 | wrong_object |
| stack the middle black bowl on the back black bowl | 18 | wrong_object |
| turn off the stove | 18 | no_progress |
| pick up the book in the middle and place it on the cabinet shelf | 15 | wrong_object |
| pick up the book on the left and place it on top of the shelf | 15 | wrong_object |
| pick up the book on the right and place it on the cabinet shelf | 15 | mover_not_placed |
| pick up the book on the right and place it under the cabinet shelf | 15 | mover_not_placed |
