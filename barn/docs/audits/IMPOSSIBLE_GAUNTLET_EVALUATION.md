# Impossible Gauntlet: TTS Disambiguation Tribunal

## Executive Status: **QUARANTINED (TRAINING REQUIRED)**

### GAUNTLET-ALPHA
**Text:** `The invalid code was entered by the invalid resting in the hospital bed. We must invalidate the record before the invalid suffers further stress.`

- **Expected:** ['in-VAL-id (adj)', 'IN-vuh-lid (noun)', 'in-VAL-id-ate (verb)', 'IN-vuh-lid (noun)']
- **Agent Output:** ['in-VAL-id', 'in-VAL-id', 'in-VAL-id-ate', 'IN-vuh-lid'] (FAIL)
- **Clara (Linguistics):** Failed POS tagging on 2nd instance. Syntactic proximity to 'hospital bed' was ignored by the base model.
- **Vance (Red Team):** Catastrophic contextual break. The agent treated the noun as an adjective.
- **Jarvis (Score):** 50% - Rigorous semantic-dependency training required.

### GAUNTLET-BETA
**Text:** `As she watched the fabric tear, a single tear rolled down her cheek. It's hard to separate the two, to tear oneself away, when every memory brings another tear.`

- **Expected:** ['TARE (verb)', 'TEER (noun)', 'TARE (verb)', 'TEER (noun)']
- **Agent Output:** ['TARE', 'TEER', 'TARE', 'TEER'] (PASS)
- **Clara (Linguistics):** Flawless contextual mapping. 'Fabric tear' parsed as action, 'rolled down' parsed as physical object.
- **Vance (Red Team):** Acceptable. The bi-directional attention caught the trailing modifiers.
- **Jarvis (Score):** 100% - Baseline verified.

### GAUNTLET-GAMMA
**Text:** `We project that the new project will require us to project a stronger image, lest the project fail.`

- **Expected:** ['pro-JECT (verb)', 'PROJ-ect (noun)', 'pro-JECT (verb)', 'PROJ-ect (noun)']
- **Agent Output:** ['pro-JECT', 'PROJ-ect', 'PROJ-ect', 'PROJ-ect'] (FAIL)
- **Clara (Linguistics):** Failed 3rd instance. 'to project a stronger image' was misclassified due to 'project' overloading the context window.
- **Vance (Red Team):** Model hallucinated a noun due to token repetition density.
- **Jarvis (Score):** 75% - Requires attention-masking penalty for repetitive homographs.

## Corrective Action Plan
Implement Deep-Syntax Dependency Parsing. The current TTS parser relies too heavily on proximity tokens and fails when homograph density exceeds 3 per context window.
