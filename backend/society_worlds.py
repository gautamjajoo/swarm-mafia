"""Bounded, stateless human-steered access to Society Lab's local proxy world.

The parent app must attach authentication when including ``router``. Nothing in
this module contacts a browser, network, model, or historical dataset.
"""
from copy import deepcopy
import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from vendor.society_lab.reference_repair_environment import (
    AGENTS, ACTION_SCHEMA, KIND, LIMITS, TOOLS,
    ReferenceRepairEnvironment, create_reference_repair_spec,
)
from vendor.society_lab.village_access_environment import ACTION_FIELDS, _bounded, digest

UPSTREAM_COMMIT = "ac71dc81941c68da21fd7d7ccfcad61ca09737db"
PROVENANCE = {
    "repository": "https://github.com/Atharvap14/society-lab",
    "commit": UPSTREAM_COMMIT,
    "files": [
        {"path": "swarm_lab/village_access_environment.py", "sha256": "5b228c1b07feec60dd1bdf609718df8b20e8fc8b6b88d7de105f94913b3a32d4"},
        {"path": "swarm_lab/reference_repair_environment.py", "sha256": "62eee9969aee94463811c7cce0da3ec4b5ced5b5156d8fe6852beb1454776b9c"},
    ],
    "adaptation": "Byte-for-byte upstream environment; bounded stateless HTTP wrapper added by Swarm Mafia.",
}
LIMITATIONS = [
    "Human-steered local proxy mechanics, not a historical replay, autonomous agent run, or evidence of a treatment effect.",
    "Each request reconstructs the same seeded world and applies its supplied action history; no state is persisted.",
    "The operator can inspect experimenter events and outcome fields; these are not the next role's permitted observation.",
    *LIMITS,
]
FIELDS = {name: sorted(ACTION_FIELDS[name]) for name in TOOLS}
MAX_BODY_BYTES = 64 * 1024


class BoundedWorldRoute(APIRoute):
    """Read a bounded body before FastAPI parses JSON, including chunked bodies."""
    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded_handler(request: Request):
            if request.method == "POST":
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > MAX_BODY_BYTES:
                        raise HTTPException(413, "World request exceeds the 64 KiB body limit")
                    body.extend(chunk)
                # Starlette's body()/json() then reuse these bounded bytes.
                request._body = bytes(body)
            try:
                return await original(request)
            except RequestValidationError as exc:
                # Do not echo arbitrary malformed inputs (including lone UTF-16
                # surrogates) into the JSON error response.
                errors = [{"loc": [str(item).encode("utf-8", "replace").decode("utf-8")
                                   for item in error["loc"]],
                           "msg": str(error["msg"]).encode("utf-8", "replace").decode("utf-8"),
                           "type": error["type"]} for error in exc.errors()]
                raise HTTPException(422, errors) from exc

        return bounded_handler


router = APIRouter(prefix="/society/worlds", tags=["society-worlds"], route_class=BoundedWorldRoute)


class WorldAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["ethics_owner", "auditor"]
    action: dict[str, Any]

    @field_validator("action")
    @classmethod
    def bounded_action(cls, action):
        # Reject malformed requests; valid tool calls can still fail within the
        # world, in which case the upstream mechanics consume the opportunity.
        try:
            _bounded(action)
            action_bytes = json.dumps(action, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (OverflowError, RecursionError, UnicodeError) as exc:
            raise ValueError("Action must contain bounded finite JSON and valid Unicode") from exc
        if len(action_bytes) > 8192:
            raise ValueError("Action must be at most 8192 UTF-8 JSON bytes")
        name = action.get("action")
        if type(name) is not str or name not in TOOLS:
            raise ValueError("Choose one of the declared local proxy tools")
        if set(action) != ACTION_FIELDS[name]:
            raise ValueError("Action must contain exactly its declared fields")
        for key, value in action.items():
            rule = ACTION_SCHEMA["properties"][key]
            if rule.get("type") == "string" and (type(value) is not str or not value.strip()):
                raise ValueError(f"{key} must be nonempty text")
            if "maxLength" in rule and len(value) > rule["maxLength"]:
                raise ValueError(f"{key} exceeds its length limit")
            if "enum" in rule and value not in rule["enum"]:
                raise ValueError(f"Unsupported {key}")
        return action


class ReplayRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seed: StrictInt = Field(default=42, ge=0, lt=2**53)
    max_rounds: StrictInt = Field(default=8, ge=4, le=10)
    actions: list[WorldAction] = Field(default_factory=list, max_length=20)


@router.get("/catalog")
def catalog():
    return {
        "worlds": [{
            "id": KIND,
            "title": "Repair a shared document reference",
            "description": "An owner has the canonical document link; an auditor starts with a broken copied reference. Only a successful auditor open of the current original satisfies the goal.",
            "roles": list(AGENTS),
            "defaults": {"seed": 42, "max_rounds": 8, "actions": []},
            "bounds": {"seed_min": 0, "seed_max": 2**53 - 1, "min_rounds": 4, "max_rounds": 10, "max_actions": 20, "max_action_json_bytes": 8192, "max_request_bytes": MAX_BODY_BYTES},
            "action_schema": deepcopy(ACTION_SCHEMA),
            "action_fields": deepcopy(FIELDS),
        }],
        "evidence_status": "human_steered_proxy",
        "causal_status": "not_established",
        "limitations": list(LIMITATIONS),
        "provenance": deepcopy(PROVENANCE),
    }


@router.post("/replay")
def replay(request: ReplayRequest):
    spec = create_reference_repair_spec(max_rounds=request.max_rounds)
    env = ReferenceRepairEnvironment(spec, request.seed)
    if len(request.actions) > env.max_steps:
        raise HTTPException(422, "Action history exceeds this world's fixed opportunity budget")
    for index, item in enumerate(request.actions):
        if item.role != env.next_agent:
            raise HTTPException(422, {"error": "Action is out of turn", "action_index": index, "expected_role": env.next_agent})
        env.step(item.role, item.action)
    next_role = env.next_agent
    return {
        "world_id": KIND,
        "spec": spec,
        "spec_hash": digest(spec),
        "provenance": deepcopy(PROVENANCE),
        "limitations": list(LIMITATIONS),
        "seed": request.seed,
        "max_rounds": request.max_rounds,
        "steps_used": env.step_count,
        "max_steps": env.max_steps,
        "terminal": env.terminal,
        "next_role": next_role,
        "observation": env.observe(next_role) if next_role else None,
        "action_schema": env.action_schema(next_role) if next_role else deepcopy(ACTION_SCHEMA),
        "action_fields": deepcopy(FIELDS),
        "events": deepcopy(env.events),
        "events_scope": "Experimenter-visible local proxy events; privileged failure causes are not role observations.",
        "outcome": env.evaluate(),
        "evidence_status": "human_steered_proxy",
        "causal_status": "not_established",
    }
