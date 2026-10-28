"""Build a reviewable full-story blocking package; never self-approve."""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import math
import re
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def fingerprint(plan):
    return hashlib.sha256(json.dumps(plan, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode("utf-8")).hexdigest()


def validate(plan):
    actors = plan["characters"]
    ids = [a["id"] for a in actors]
    nodes = plan["nodes"]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError("Character IDs must be nonempty and unique")
    if len(nodes) < 2 or len({n["id"] for n in nodes}) != len(nodes):
        raise ValueError("At least two uniquely named story nodes are required")
    for actor in actors:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", actor["color"]):
            raise ValueError("Use #RRGGBB identity colors")
    for node in nodes:
        if set(node["states"]) != set(ids):
            raise ValueError(f"{node['id']}: every registered character needs a state, including offscreen actors")
        for actor_id, state in node["states"].items():
            xyz = state["position"]
            if len(xyz) != 3 or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in xyz):
                raise ValueError(f"{node['id']}/{actor_id}: finite feet-level xyz required")
            for key in ("intent", "facing", "visibility", "level"):
                if not str(state.get(key, "")).strip():
                    raise ValueError(f"{node['id']}/{actor_id}: missing {key}")
    transitions = plan["transitions"]
    if len(transitions) != len(nodes) - 1:
        raise ValueError("One transition for each adjacent pair of nodes is required")
    for i, transition in enumerate(transitions):
        if (transition["from"], transition["to"]) != (nodes[i]["id"], nodes[i+1]["id"]):
            raise ValueError("Transitions must preserve story-node order")
        if set(transition["characters"]) != set(ids):
            raise ValueError("Each transition needs every actor, including HOLD")
        for actor_id, route in transition["characters"].items():
            points = route["points"]
            if route["mode"] not in ("MOVE", "HOLD") or len(points) < 2:
                raise ValueError("Route mode must be MOVE or HOLD with at least two points")
            if any(len(p) != 3 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in p) for p in points):
                raise ValueError("Route points must be finite xyz")
            start, end = nodes[i]["states"][actor_id]["position"], nodes[i+1]["states"][actor_id]["position"]
            if math.dist(points[0], start) > 1e-5 or math.dist(points[-1], end) > 1e-5:
                raise ValueError(f"{actor_id}: route endpoints do not match node positions")
            if route["mode"] == "HOLD" and any(math.dist(p, start)>1e-5 for p in points):
                raise ValueError("HOLD cannot move a character")
    return plan


def check_approval(plan, decision):
    if decision.get("status") != "confirmed":
        return False, "User confirmation is pending"
    if decision.get("plan_sha256") != fingerprint(plan):
        return False, "Plan changed; previous confirmation is stale"
    if decision.get("scope") != "whole_story_routes_and_key_positions":
        return False, "Confirmation does not cover the whole-story route/position scope"
    if not all(str(decision.get(k, "")).strip() for k in ("user_message", "message_source", "confirmed_at")):
        return False, "Actual user confirmation evidence is missing"
    return True, "Recorded confirmation matches this plan; verify message authenticity in the conversation"


def svg_map(plan, title, nodes, transitions):
    points = [s["position"] for n in plan["nodes"] for s in n["states"].values()]
    points += [p for t in plan["transitions"] for r in t["characters"].values() for p in r["points"]]
    xmin,xmax=min(p[0] for p in points)-2,max(p[0] for p in points)+2
    ymin,ymax=min(p[1] for p in points)-2,max(p[1] for p in points)+2
    scale=min(710/(xmax-xmin),570/(ymax-ymin))
    def xy(p):return 45+(p[0]-xmin)*scale,675-(p[1]-ymin)*scale
    def label(x,y,text,size=15):return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}">{html.escape(str(text))}</text>'
    height=max(740,130+len(plan["characters"])*40)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="{height}" viewBox="0 0 1100 {height}">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<style>text{font-family:Microsoft YaHei,Arial,sans-serif;fill:#20262b}</style>',
         '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#586570"/></marker></defs>',
         label(35,36,title,23),label(35,65,"+X →   +Y ↑     XY plan; check elevations and scene occlusion separately",15),
         '<rect x="30" y="95" width="735" height="605" fill="#f5f7f8" stroke="#cbd2d7"/>']
    for a in plan.get("landmarks",[]):
        x,y=xy(a["position"]);out.append(label(x,y,a["name"],13))
    for i,a in enumerate(plan["characters"],1):
        aid,c=a["id"],a["color"]
        out.append(f'<circle cx="805" cy="{105+i*36}" r="9" fill="{c}"/>')
        out.append(label(824,110+i*36,f"{i}  {a['name']}",16))
        for t in transitions:
            r=t["characters"][aid]
            if r["mode"]=="MOVE":
                coords=" ".join(f"{xy(p)[0]:.1f},{xy(p)[1]:.1f}" for p in r["points"])
                out.append(f'<polyline points="{coords}" fill="none" stroke="{c}" stroke-width="2.5" opacity=".7" marker-end="url(#arrow)"/>')
        for n in nodes:
            x,y=xy(n["states"][aid]["position"])
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{c}" stroke="white"/>')
            out.append(label(x+11,y-8,str(i),14))
    out.append(label(35,725,"Diagram draft • terrain and camera visibility require scene-context review",14))
    return "\n".join(out+["</svg>"])


def build(plan, output):
    validate(plan)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    sha=fingerprint(plan)
    maps=[("overview.svg", "Whole story routes", plan["nodes"], plan["transitions"])]
    maps += [(f"node_{i+1:02d}.svg",f"{i+1}  {n['label']}",[n],[]) for i,n in enumerate(plan["nodes"])]
    maps += [(f"route_{i+1:02d}.svg",f"{t['from']} → {t['to']}",[plan["nodes"][i],plan["nodes"][i+1]],[t])
             for i,t in enumerate(plan["transitions"])]
    for name,title,nodes,trans in maps:
        (output/name).write_text(svg_map(plan,title,nodes,trans),encoding="utf-8")
    with (output/"character-node-table.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f);writer.writerow(["actor","node","time_or_order","intent","x","y","z","level","facing","visibility"])
        for a in plan["characters"]:
            for n in plan["nodes"]:
                s=n["states"][a["id"]]
                writer.writerow([a["name"],n["label"],n.get("time_or_order",""),s["intent"],*s["position"],s["level"],s["facing"],s["visibility"]])
    page=['<!doctype html><meta charset="utf-8"><title>Story blocking review</title>',
          '<style>body{font:18px sans-serif;max-width:1150px;margin:32px auto;color:#20262b}img{width:100%;border:1px solid #ddd}p{line-height:1.6}</style>',
          f'<h1>{html.escape(plan["project_id"])} · {html.escape(plan["revision"])}</h1>',
          '<p>待使用者确认全场路线与关键站位。此页不会自动批准。查看每个角色的终点、朝向、高度、离画去向，并结合真实场景图检查遮挡。</p>',
          f'<p>Plan SHA256: {sha}</p><p><a href="character-node-table.csv">逐角色节点表</a></p>']
    for name,title,_,_ in maps:
        page += [f"<h2>{html.escape(title)}</h2>",f'<img src="{name}" alt="{html.escape(title)}">']
    (output/"review.html").write_text("\n".join(page),encoding="utf-8")
    manifest={"project_id":plan["project_id"],"revision":plan["revision"],"plan_sha256":sha,
              "characters":len(plan["characters"]),"nodes":len(plan["nodes"]),"status":"awaiting_user_confirmation",
              "scope":"whole_story_routes_and_key_positions"}
    (output/"review-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("plan",type=Path)
    p.add_argument("--output",type=Path);p.add_argument("--check-approval",type=Path)
    a=p.parse_args();plan=validate(load(a.plan))
    if a.output:print(json.dumps(build(plan,a.output),ensure_ascii=False))
    if a.check_approval:
        ok,message=check_approval(plan,load(a.check_approval));print(message)
        if not ok:raise SystemExit(2)
    if not a.output and not a.check_approval:p.error("Specify --output and/or --check-approval")


if __name__=="__main__":main()
