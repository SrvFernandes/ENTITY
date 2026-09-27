from __future__ import annotations
from pathlib import Path
from typing import Any
import hashlib, json, secrets, sqlite3, time

from reality_profile import CAUSAL_NODE_TYPES, CAUSAL_EDGE_TYPES

def now_ms() -> int:
    return int(time.time() * 1000)

def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode()

def digest(value: Any) -> str:
    return hashlib.sha256(canon(value)).hexdigest()

def rid(prefix: str) -> str:
    return prefix + "-" + secrets.token_hex(12)

class CausalEconomicAttributionGraph:
    """Evidence-bound causal lineage from source information to economic consequence."""
    def __init__(self, root: str | Path, identity):
        self.path = Path(root) / "entity_v3_3_causal_economy.sqlite"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.identity = identity
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS nodes(
                node_id TEXT PRIMARY KEY, node_type TEXT NOT NULL, ref_id TEXT NOT NULL,
                controller_entity_id TEXT NOT NULL, body_json TEXT NOT NULL,
                signature_json TEXT NOT NULL, created_at_ms INTEGER NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS edges(
                edge_id TEXT PRIMARY KEY, from_node_id TEXT NOT NULL, to_node_id TEXT NOT NULL,
                edge_type TEXT NOT NULL, body_json TEXT NOT NULL, signature_json TEXT NOT NULL,
                created_at_ms INTEGER NOT NULL)""")

    def add_node(self, controller_entity_id: str, node_type: str, ref_id: str,
                 *, evidence_refs: list[str] | None = None, event_refs: list[str] | None = None,
                 economic_observation: dict | None = None) -> dict:
        self.identity.load_manifest(controller_entity_id)
        node_type = str(node_type).upper()
        if node_type not in CAUSAL_NODE_TYPES:
            raise ValueError("unsupported causal node type")
        observation = dict(economic_observation or {})
        if observation:
            observation["market_observation_is_not_accounting_fair_value"] = True
            observation["protocol_does_not_determine_legal_entitlement"] = True
        body = {
            "schema": "entity-v3-causal-economic-node-v1",
            "node_id": rid("causalnode3"),
            "node_type": node_type,
            "ref_id": str(ref_id),
            "controller_entity_id": controller_entity_id,
            "evidence_refs": sorted({str(x) for x in (evidence_refs or [])}),
            "event_refs": sorted({str(x) for x in (event_refs or [])}),
            "economic_observation": observation,
            "created_at_ms": now_ms(),
        }
        sig = self.identity.sign(controller_entity_id, body)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO nodes VALUES(?,?,?,?,?,?,?)", (
                body["node_id"], node_type, body["ref_id"], controller_entity_id,
                json.dumps(body, sort_keys=True), json.dumps(sig, sort_keys=True), body["created_at_ms"]))
        return dict(body, signature=sig)

    def _node_exists(self, node_id: str) -> bool:
        with sqlite3.connect(self.path) as db:
            return db.execute("SELECT 1 FROM nodes WHERE node_id=?", (node_id,)).fetchone() is not None

    def _would_cycle(self, from_node_id: str, to_node_id: str) -> bool:
        if from_node_id == to_node_id:
            return True
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT from_node_id,to_node_id FROM edges").fetchall()
        adj: dict[str, list[str]] = {}
        for a, b in rows:
            adj.setdefault(a, []).append(b)
        stack = [to_node_id]
        seen = set()
        while stack:
            node = stack.pop()
            if node == from_node_id:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(adj.get(node, []))
        return False

    def add_edge(self, actor_entity_id: str, from_node_id: str, to_node_id: str,
                 edge_type: str, *, evidence_refs: list[str], authority_refs: list[str] | None = None,
                 participation_rule_refs: list[str] | None = None) -> dict:
        self.identity.load_manifest(actor_entity_id)
        edge_type = str(edge_type).upper()
        if edge_type not in CAUSAL_EDGE_TYPES:
            raise ValueError("unsupported causal edge type")
        if not self._node_exists(from_node_id) or not self._node_exists(to_node_id):
            raise KeyError("causal node missing")
        if self._would_cycle(from_node_id, to_node_id):
            raise ValueError("causal graph must remain acyclic")
        refs = sorted({str(x) for x in evidence_refs if str(x)})
        if not refs:
            raise ValueError("causal edge requires evidence")
        body = {
            "schema": "entity-v3-causal-economic-edge-v1",
            "edge_id": rid("causedge3"),
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "edge_type": edge_type,
            "actor_entity_id": actor_entity_id,
            "evidence_refs": refs,
            "authority_refs": sorted({str(x) for x in (authority_refs or [])}),
            "participation_rule_refs": sorted({str(x) for x in (participation_rule_refs or [])}),
            "causality_is_evidence_bound_not_assumed": True,
            "economic_attribution_is_not_accounting_fair_value": True,
            "created_at_ms": now_ms(),
        }
        sig = self.identity.sign(actor_entity_id, body)
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO edges VALUES(?,?,?,?,?,?,?)", (
                body["edge_id"], from_node_id, to_node_id, edge_type,
                json.dumps(body, sort_keys=True), json.dumps(sig, sort_keys=True), body["created_at_ms"]))
        return dict(body, signature=sig)

    def trace(self, source_node_id: str, target_node_id: str) -> dict:
        source_node_id = str(source_node_id)
        target_node_id = str(target_node_id)
        if (not source_node_id or not target_node_id or
                not self._node_exists(source_node_id) or
                not self._node_exists(target_node_id)):
            return {
                "connected": False,
                "path": [],
                "path_sha256": digest([]),
                "causal_chain_is_evidence_bound": False,
                "economic_attribution_is_not_accounting_fair_value": True,
                "endpoints_valid": False,
            }
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM edges ORDER BY created_at_ms,edge_id").fetchall()
        edges = [json.loads(row["body_json"]) for row in rows]
        adj: dict[str, list[dict]] = {}
        for edge in edges:
            adj.setdefault(edge["from_node_id"], []).append(edge)
        queue = [(source_node_id, [])]
        seen = set()
        while queue:
            node, path = queue.pop(0)
            if node == target_node_id:
                return {
                    "connected": True,
                    "path": path,
                    "path_sha256": digest(path),
                    "causal_chain_is_evidence_bound": bool(path) and all(bool(edge["evidence_refs"]) for edge in path),
                    "economic_attribution_is_not_accounting_fair_value": True,
                    "endpoints_valid": True,
                }
            if node in seen:
                continue
            seen.add(node)
            for edge in adj.get(node, []):
                queue.append((edge["to_node_id"], path + [edge]))
        return {
            "connected": False,
            "path": [],
            "path_sha256": digest([]),
            "causal_chain_is_evidence_bound": False,
            "economic_attribution_is_not_accounting_fair_value": True,
            "endpoints_valid": True,
        }

    def graph_root(self) -> str:
        with sqlite3.connect(self.path) as db:
            nodes = [json.loads(row[0]) for row in db.execute("SELECT body_json FROM nodes ORDER BY node_id")]
            edges = [json.loads(row[0]) for row in db.execute("SELECT body_json FROM edges ORDER BY edge_id")]
        return digest({"nodes": nodes, "edges": edges})
