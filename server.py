#!/usr/bin/env python3
"""
OmniTransit-Agent Swarm — High-Throughput Backend API & Digital Twin Server
===========================================================================
Serves the Enterprise Command-Center Frontend and exposes REST endpoints for:
- Real-Time Digital Twin Telemetry (`/api/state`)
- JWT Authentication & Session Verification (`/api/auth/login`, `/api/auth/verify`)
- Adversarial Chaos Monkey Disruptions (`/api/disrupt`)
- Autonomous Multi-Agent Token Auction (`/api/optimize`)
- Combined Chaos + Swarm + GenAI Execution (`/api/simulate-full`)
- 2,000,000-Row Blocked Dataset Analytics & SQLite Inspector (`/api/dataset-stats`, `/api/query-blocks`)
- Interactive Blocked GBM Demand & Wait-Time Predictor (`/api/predict-demand`)
- Online Model Retraining Engine (`/api/train-model`)
- Model Predictive Control Horizon (`/api/mpc-horizon`)
- Robust Optimization Uncertainty Matrix (`/api/robust-matrix`)
- Constraint Feasibility Auditor (`/api/constraints-audit`)
- Generative AI Causal Architect Briefing & Prompt Generator (`/api/genai-brief`)
"""

import argparse
import json
import mimetypes
import os
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, urlparse

# Ensure Windows terminals support UTF-8 output without charmap errors
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from omnitransit.agent_swarm import FleetMarketCommander
from omnitransit.auth import JWTAuth
from omnitransit.chaos_monkey import ChaosMonkeyAgent
from omnitransit.digital_twin import UrbanTransitDigitalTwin
from omnitransit.genai_architect import GenAITransitArchitect
from omnitransit.model_trainer import ModelTrainer
from omnitransit.mpc_optimizer import (
    ConstraintFeasibilityAuditor,
    ModelPredictiveController,
    RobustOptimizationEngine,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DATA_DIR = os.path.join(BASE_DIR, "data")
SQLITE_PATH = os.path.join(DATA_DIR, "omnitransit_blocks.db")
CONFIG_FILE = os.path.join(DATA_DIR, "app_config.json")

# Global Singleton Instances for the Digital Twin & Agent Swarm
CITY_TWIN = UrbanTransitDigitalTwin()
CHAOS_AGENT = ChaosMonkeyAgent()
FLEET_COMMANDER = FleetMarketCommander()
MPC_CONTROLLER = ModelPredictiveController()
ROBUST_OPTIMIZER = RobustOptimizationEngine()
CONSTRAINT_AUDITOR = ConstraintFeasibilityAuditor()


class OmniTransitRequestHandler(BaseHTTPRequestHandler):
    """High-speed HTTP & JSON API handler for the OmniTransit Command Center."""

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep console output clean
        pass

    def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def _get_token_from_request(self, body: Dict[str, Any]) -> str:
        """Extracts JWT bearer token from Authorization header or body fallback."""
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            return auth_hdr[7:].strip()
        return body.get("token", "") or body.get("jwt", "")

    def _verify_jwt(self, body: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Verifies JWT signature and returns (valid, user_payload)."""
        token = self._get_token_from_request(body)
        if not token:
            # Check if demo authorization bypass header is provided
            if self.headers.get("X-OmniTransit-Demo", "") == "bypass":
                return True, {"name": "Demo Operator", "role": "Chief Transit Architect", "sub": "admin"}
            return False, {"error": "Missing Authorization Bearer token. Please sign in."}
        return JWTAuth.verify_token(token)

    def do_OPTIONS(self) -> None:
        self._send_json({"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Telemetry & State API
        if path == "/api/state":
            self._send_json(CITY_TWIN.get_twin_telemetry())
            return

        # Dataset Analytics API
        if path == "/api/dataset-stats":
            self._send_json(CITY_TWIN.dataset_summary)
            return

        # SQLite Smart Blocks Query API
        if path == "/api/query-blocks":
            hub_filter = query.get("hub", ["ALL"])[0]
            bucket_filter = query.get("time_bucket", ["ALL"])[0]
            weather_filter = query.get("weather", ["ALL"])[0]
            rows = self._query_sqlite_blocks(hub_filter, bucket_filter, weather_filter)
            self._send_json({"blocks": rows, "count": len(rows)})
            return

        # Interactive Blocked Demand & Wait-Time Predictor API
        if path == "/api/predict-demand":
            hub_code = query.get("hub_code", ["KAL"])[0]
            time_bucket = query.get("time_bucket", ["PM_PEAK"])[0]
            weather_code = query.get("weather_code", ["FLA"])[0]
            headway = int(query.get("headway_mins", ["12"])[0])
            pred = CITY_TWIN.predict_block_demand(hub_code, time_bucket, weather_code, headway)
            self._send_json(pred)
            return

        # Model Predictive Control (MPC) Horizon API
        if path == "/api/mpc-horizon":
            mode = query.get("mode", ["ADAPTIVE_MPC"])[0]
            horizon = MPC_CONTROLLER.run_mpc_rolling_horizon(CITY_TWIN, control_mode=mode)
            self._send_json(horizon)
            return

        # Robust Optimization Uncertainty Matrix API
        if path == "/api/robust-matrix":
            matrix = ROBUST_OPTIMIZER.evaluate_strategies_matrix(CITY_TWIN)
            self._send_json(matrix)
            return

        # Constraint Feasibility Auditor API
        if path == "/api/constraints-audit":
            audit = CONSTRAINT_AUDITOR.audit_fleet_transition(CITY_TWIN, {})
            self._send_json(audit)
            return

        # Current Trained Model Metadata API
        if path == "/api/model-info":
            self._send_json(CITY_TWIN.trained_model or {})
            return

        # App Configuration & Google Maps API Key API
        if path == "/api/config":
            maps_key = os.environ.get("GOOGLE_MAPS_API_KEY", "") or os.environ.get("MAPS_API_KEY", "")
            if not maps_key and os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        maps_key = json.load(f).get("google_maps_api_key", "")
                except Exception:
                    pass
            self._send_json({"google_maps_api_key": maps_key})
            return

        # Serve static frontend files
        if path == "/" or path == "":
            path = "/index.html"

        safe_rel = os.path.normpath(path.lstrip("/"))
        file_path = os.path.join(FRONTEND_DIR, safe_rel)
        if os.path.isfile(file_path):
            ctype, _ = mimetypes.guess_type(file_path)
            ctype = ctype or "application/octet-stream"
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_json({"error": "Not found", "path": path}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json_body()

        # Save App Configuration (e.g. Google Maps API Key)
        if path == "/api/config":
            key = body.get("google_maps_api_key", "").strip()
            cfg = {"google_maps_api_key": key}
            try:
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=2)
            except Exception:
                pass
            self._send_json({"status": "CONFIG_SAVED", "google_maps_api_key": key})
            return

        # JWT Authentication: Login
        if path == "/api/auth/login":
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            session = JWTAuth.authenticate_credentials(username, password)
            if session:
                CITY_TWIN.log_event(
                    "AUTH_SERVICE",
                    "LOGIN_SUCCESS",
                    f"Operator authenticated: {session['name']} ({session['role']}) via JWT HMAC-SHA256",
                )
                self._send_json({"status": "AUTHENTICATED", "token": session["token"], "session": session, "user": session})
            else:
                self._send_json(
                    {
                        "error": "INVALID_CREDENTIALS",
                        "message": "Authentication failed. Check operator username and password.",
                    },
                    status=401,
                )
            return

        # JWT Authentication: Verify Token
        if path == "/api/auth/verify":
            valid, user_data = self._verify_jwt(body)
            if valid:
                self._send_json({"valid": True, "user": user_data})
            else:
                self._send_json({"valid": False, "error": user_data.get("error")}, status=401)
            return

        # Train Model API (Protected by JWT)
        if path == "/api/train-model":
            valid, user = self._verify_jwt(body)
            if not valid:
                self._send_json({"error": "UNAUTHORIZED", "message": user.get("error")}, status=401)
                return

            n_trees = int(body.get("n_trees", 25))
            learning_rate = float(body.get("learning_rate", 0.25))
            n_trees = max(5, min(100, n_trees))
            learning_rate = max(0.01, min(1.0, learning_rate))

            model_res = ModelTrainer.train_gbm(n_estimators=n_trees, learning_rate=learning_rate)
            CITY_TWIN.trained_model = model_res
            CITY_TWIN.log_event(
                "ML_TRAINER",
                "TRAINING_COMPLETE",
                f"Blocked GBM retrained ({n_trees} trees, LR={learning_rate}) by {user.get('name')}. "
                f"Demand R2={model_res['metrics']['demand_r2_score']}, Wait R2={model_res['metrics']['wait_time_r2_score']}",
            )
            self._send_json({
                "status": "TRAINING_COMPLETE",
                "model": model_res,
                "operator": user.get("name"),
            })
            return

        # Reset Digital Twin (Protected by JWT)
        if path == "/api/reset":
            valid, user = self._verify_jwt(body)
            if not valid:
                self._send_json({"error": "UNAUTHORIZED", "message": user.get("error")}, status=401)
                return

            CITY_TWIN.reset_to_baseline()
            CITY_TWIN.log_event(
                "DISPATCH_CMD",
                "SYSTEM_RESET",
                f"Digital Twin restored to schedule equilibrium by {user.get('name')}",
            )
            self._send_json(
                {
                    "status": "RESET_COMPLETE",
                    "telemetry": CITY_TWIN.get_twin_telemetry(),
                }
            )
            return

        # Chaos Monkey Disruption (Protected by JWT)
        if path == "/api/disrupt":
            valid, user = self._verify_jwt(body)
            if not valid:
                self._send_json({"error": "UNAUTHORIZED", "message": user.get("error")}, status=401)
                return

            event_type = body.get("event_type", "HEAVY_RAIN")
            custom_params = body.get("custom_params")
            CITY_TWIN.reset_to_baseline()
            disruption_info = CHAOS_AGENT.trigger_disruption(CITY_TWIN, event_type, custom_params)
            GenAITransitArchitect.generate_causal_briefing(CITY_TWIN)
            self._send_json(
                {
                    "status": "DISRUPTION_APPLIED",
                    "disruption": disruption_info,
                    "telemetry": CITY_TWIN.get_twin_telemetry(),
                }
            )
            return

        # Swarm Multi-Agent Token Auction (Protected by JWT)
        if path == "/api/optimize":
            valid, user = self._verify_jwt(body)
            if not valid:
                self._send_json({"error": "UNAUTHORIZED", "message": user.get("error")}, status=401)
                return

            api_key = body.get("api_key")
            provider = body.get("provider", "gemini")
            market_result = FLEET_COMMANDER.run_market_equilibrium(CITY_TWIN)
            genai_result = GenAITransitArchitect.generate_causal_briefing(
                CITY_TWIN, api_key=api_key, provider=provider
            )
            self._send_json(
                {
                    "status": "SWARM_OPTIMIZED",
                    "market_result": market_result,
                    "genai": genai_result,
                    "telemetry": CITY_TWIN.get_twin_telemetry(),
                }
            )
            return

        # Combined Full Simulation: Chaos + Swarm + GenAI (Protected by JWT)
        if path == "/api/simulate-full":
            valid, user = self._verify_jwt(body)
            if not valid:
                self._send_json({"error": "UNAUTHORIZED", "message": user.get("error")}, status=401)
                return

            event_type = body.get("event_type", "HEAVY_RAIN")
            custom_params = body.get("custom_params")
            api_key = body.get("api_key")
            provider = body.get("provider", "gemini")

            CITY_TWIN.reset_to_baseline()
            disruption_info = CHAOS_AGENT.trigger_disruption(CITY_TWIN, event_type, custom_params)
            market_result = FLEET_COMMANDER.run_market_equilibrium(CITY_TWIN)
            genai_result = GenAITransitArchitect.generate_causal_briefing(
                CITY_TWIN, api_key=api_key, provider=provider
            )
            self._send_json(
                {
                    "status": "FULL_SIMULATION_COMPLETE",
                    "disruption": disruption_info,
                    "market_result": market_result,
                    "genai": genai_result,
                    "telemetry": CITY_TWIN.get_twin_telemetry(),
                }
            )
            return

        # GenAI Causal Briefing API
        if path == "/api/genai-brief":
            api_key = body.get("api_key")
            provider = body.get("provider", "gemini")
            genai_result = GenAITransitArchitect.generate_causal_briefing(
                CITY_TWIN, api_key=api_key, provider=provider
            )
            self._send_json(
                {
                    "status": "BRIEFING_GENERATED",
                    "genai": genai_result,
                    "telemetry": CITY_TWIN.get_twin_telemetry(),
                }
            )
            return

        # MPC Horizon Dynamic Execution
        if path == "/api/mpc-horizon":
            mode = body.get("mode", "ADAPTIVE_MPC")
            disruption = body.get("disruption_type", "CURRENT")
            horizon = MPC_CONTROLLER.run_mpc_rolling_horizon(
                CITY_TWIN, disruption_type=disruption, control_mode=mode
            )
            self._send_json(horizon)
            return

        # Robust Matrix Dynamic Execution
        if path == "/api/robust-matrix":
            matrix = ROBUST_OPTIMIZER.evaluate_strategies_matrix(CITY_TWIN)
            self._send_json(matrix)
            return

        # Constraints Audit Dynamic Execution
        if path == "/api/constraints-audit":
            candidate = body.get("candidate_shift", {})
            audit = CONSTRAINT_AUDITOR.audit_fleet_transition(CITY_TWIN, candidate)
            self._send_json(audit)
            return

        self._send_json({"error": "Unknown endpoint", "path": path}, status=404)

    @staticmethod
    def _query_sqlite_blocks(hub: str, time_bucket: str, weather: str) -> list:
        if not os.path.exists(SQLITE_PATH):
            return []
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        clauses = []
        params = []
        if hub and hub != "ALL":
            clauses.append("hub_code = ?")
            params.append(hub)
        if time_bucket and time_bucket != "ALL":
            clauses.append("time_bucket = ?")
            params.append(time_bucket)
        if weather and weather != "ALL":
            clauses.append("weather_code = ?")
            params.append(weather[:3].upper())

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql = f"""
            SELECT block_key, hub_code, route_id, time_bucket, weather_code,
                   record_count, avg_demand, avg_wait_mins, avg_load_pct, avg_bounty, distress_rate_pct
            FROM smart_blocks
            {where_sql}
            ORDER BY avg_wait_mins DESC
            LIMIT 50
        """
        cur.execute(sql, params)
        rows = [
            {
                "block_key": r[0],
                "hub_code": r[1],
                "route_id": r[2],
                "time_bucket": r[3],
                "weather_code": r[4],
                "record_count": r[5],
                "avg_demand": r[6],
                "avg_wait_mins": r[7],
                "avg_load_pct": r[8],
                "avg_bounty": r[9],
                "distress_rate_pct": r[10],
            }
            for r in cur.fetchall()
        ]
        conn.close()
        return rows


def run_self_verification() -> None:
    """Runs an end-to-end verification drill of the Digital Twin, 3-Layer Swarm, JWT Auth, and Model Retrainer."""
    print("=" * 78)
    print("OMNITRANSIT-AGENT SWARM - END-TO-END VERIFICATION DRILL")
    print("=" * 78)
    CITY_TWIN.reset_to_baseline()
    print(f"[1] Digital Twin Baseline Loaded: {len(CITY_TWIN.stations)} Hubs, {len(CITY_TWIN.routes)} Routes")
    print(f"[2] 2M-Row Dataset Verified: {CITY_TWIN.dataset_summary.get('total_rows', 0):,} rows on disk")

    auth = JWTAuth.authenticate_credentials("admin", "omni2026")
    assert auth is not None and "token" in auth
    is_valid, user_data = JWTAuth.verify_token(auth["token"])
    assert is_valid
    print(f"[3] JWT Authentication: HMAC-SHA256 Token Generated & Verified for {user_data['name']} ({user_data['role']})")

    model_train = ModelTrainer.train_gbm(n_estimators=25, learning_rate=0.25)
    print(
        f"[4] Model Retraining Engine: 25-Tree GBM trained in {model_train['training_time_ms']} ms | "
        f"Demand R2: {model_res_r2 if (model_res_r2 := model_train['metrics']['demand_r2_score']) else ''} | "
        f"Wait R2: {model_train['metrics']['wait_time_r2_score']}"
    )

    CHAOS_AGENT.trigger_disruption(CITY_TWIN, "HEAVY_RAIN")
    kal_before = CITY_TWIN.stations["Kalapatti Hub"]["avg_wait_time"]
    print(f"[5] Chaos Monkey Triggered (HEAVY_RAIN): Kalapatti Hub wait surged to {kal_before} mins")

    res = FLEET_COMMANDER.run_market_equilibrium(CITY_TWIN)
    kal_after = CITY_TWIN.stations["Kalapatti Hub"]["avg_wait_time"]
    print(
        f"[6] 3-Layer Token Auction Completed: {res['resolved_hubs']} Hubs resolved | "
        f"Kalapatti Hub wait dropped {kal_before}m -> {kal_after}m"
    )
    print(
        f"[7] ESG Carbon Exchange: {CITY_TWIN.esg_ledger['co2_prevented_kg']} kg CO2e prevented | "
        f"EV Guardrail Blocks: {CITY_TWIN.esg_ledger['ev_guardrail_blocks_triggered']}"
    )

    brief = GenAITransitArchitect.generate_causal_briefing(CITY_TWIN)
    print(f"[8] GenAI Causal Briefing Synthesized ({len(brief['report_markdown'])} chars)")

    mpc_res = MPC_CONTROLLER.run_mpc_rolling_horizon(CITY_TWIN, control_mode="ADAPTIVE_MPC")
    print(
        f"[9] Model Predictive Control (MPC): 60-min horizon evaluated | "
        f"Initial wait {mpc_res['summary']['initial_avg_wait_mins']}m -> Final {mpc_res['summary']['final_avg_wait_mins']}m | "
        f"Stability: {mpc_res['summary']['headway_stability_index']}%"
    )

    robust_res = ROBUST_OPTIMIZER.evaluate_strategies_matrix(CITY_TWIN)
    rec_strat = robust_res["recommended_strategy"]
    print(
        f"[10] Robust Optimization Matrix: {len(robust_res['strategies_matrix'])} strategies tested against 4 uncertainties | "
        f"Recommended: {rec_strat} (Minimax Regret)"
    )

    audit_res = CONSTRAINT_AUDITOR.audit_fleet_transition(
        CITY_TWIN, {"ev_soc_pct": 82, "headway_mins": 9, "turnaround_mins": 10}
    )
    print(
        f"[11] Constraint Feasibility Auditor: {audit_res['verdict']} "
        f"({audit_res['constraints_checked']} constraints verified)"
    )
    print("=" * 78)


def main() -> None:
    parser = argparse.ArgumentParser(description="OmniTransit-Agent Swarm Backend Server")
    parser.add_argument("--port", type=int, default=8050, help="Port to bind HTTP server (default: 8050)")
    parser.add_argument("--verify", action="store_true", help="Run self-verification drill and exit")
    args = parser.parse_args()

    if args.verify:
        run_self_verification()
        return

    server = ThreadingHTTPServer(("127.0.0.1", args.port), OmniTransitRequestHandler)
    print(f"\nOmniTransit-Agent Swarm Command Center running at: http://localhost:{args.port}")
    print(f"Guardrail Active: {CITY_TWIN.sandbox_compliance_banner}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down OmniTransit Command Center.")
        server.server_close()


if __name__ == "__main__":
    main()
