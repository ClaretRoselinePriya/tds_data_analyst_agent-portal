import json
from typing import List, Dict, Any
from agent.llm import llm_array
from agent.prompts import ANSWERER_SYSTEM, ANSWERER_USER_TEMPLATE
from app.settings import settings

_DEF_BATCH = 3

def _artefacts_excerpt(artefacts: Dict[str, Any], keys: List[str]|None=None) -> str:
    items = []
    for k, v in artefacts.items():
        if keys and k not in keys: 
            continue
        if isinstance(v, (dict, list)):
            s = json.dumps(v)[:1200]
        else:
            s = str(v)[:1200]
        items.append(f"- {k}: {s}")
    return "\n".join(items)

def batch_answer(questions: List[str], artefacts: Dict[str, Any]) -> List[Any]:
    answers = [None] * len(questions)
    for i in range(0, len(questions), _DEF_BATCH):
        idxs = list(range(i, min(i+_DEF_BATCH, len(questions))))
        qs = [questions[j] for j in idxs]
        user = ANSWERER_USER_TEMPLATE.format(
            indices=idxs,
            artefacts_excerpt=_artefacts_excerpt(artefacts)
        )
        batch = llm_array(ANSWERER_SYSTEM, user, model=settings.MODEL_ANSWERER)
        for j, val in zip(idxs, batch):
            answers[j] = val
    return answers
