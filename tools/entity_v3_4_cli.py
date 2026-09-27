from __future__ import annotations
import argparse, hashlib, importlib.util, json, pathlib, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(name,rel):
    spec=importlib.util.spec_from_file_location(name,ROOT/rel); mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

identity_mod=load("cli_v34_identity","src/01_Core_Runtime/identity/canonical_identity.py")
fabric_mod=load("cli_v34_fabric","src/30_Universal_Transaction_Fabric/canonical_universal_fabric.py")
rights_mod=load("cli_v34_rights","src/36_Adoption_Layer/rights_passport.py")
reality_profile=load("reality_profile","src/37_Verifiable_Reality/reality_profile.py")
evidence_mod=load("cli_v34_evidence","src/37_Verifiable_Reality/evidence_objects.py")
profile_mod=load("cli_v34_profiles","src/38_Global_Passports/profile_registry.py")
industry_mod=load("cli_v34_industry","src/38_Global_Passports/industry_profiles.py")
global_mod=load("cli_v34_global","src/38_Global_Passports/global_passport.py")
origin_mod=load("cli_v34_origin","src/38_Global_Passports/protocol_origin.py")
ingest_mod=load("cli_v34_ingest","src/38_Global_Passports/continuous_ingestion.py")
package_mod=load("cli_v34_packages","src/39_Implementation_Packages/industry_packages.py")
sdk_mod=load("cli_v34_sdk","sdk/global_passport_sdk/canonical_global_passport_sdk.py")
btdu_mod=load("cli_v342_btdu","src/40_BTDU/canonical_btdu.py")
ORIGIN_BUNDLE=ROOT/"protocol"/"origin"/"ENTITY_PROTOCOL_ORIGIN_BUNDLE.json"
CURRENT_RELEASE_TAG="v3.4.3"; CURRENT_RELEASE_REF="entity-release:"+CURRENT_RELEASE_TAG

def _current_release_path(explicit=None):
    candidates=[pathlib.Path(explicit)] if explicit else []
    candidates += [ROOT/"ENTITY_CURRENT_RELEASE_ORIGIN.json",ROOT/"protocol"/"origin"/"ENTITY_CURRENT_RELEASE_ORIGIN.json"]
    return next((p for p in candidates if p.is_file()),None)

def runtime(state,release_origin_path=None,require_current_release=False):
    identity=identity_mod.EntityIdentityVault(state); fabric=fabric_mod.UniversalTransactionFabric(state,identity)
    evidence=evidence_mod.EvidenceRegistry(state,identity); rights=rights_mod.RightsPassportRegistry(state,identity,fabric)
    profiles=profile_mod.GlobalProfileRegistry(state,identity); origin=origin_mod.ProtocolOriginRegistry(state,identity)
    bundle=read_json(ORIGIN_BUNDLE); origin_status=origin.install_bundle(bundle,profiles)
    current_path=_current_release_path(release_origin_path); current_status=None
    if current_path: current_status=origin.install_current_release(read_json(current_path),CURRENT_RELEASE_TAG)
    if require_current_release and not current_status: raise RuntimeError("v3.4.3 current-release origin attestation required; supply --release-origin or use the signed release package")
    origin_status=dict(origin_status,current_release_origin=current_status,current_release_origin_path=str(current_path) if current_path else None)
    passports=global_mod.GlobalPassportRegistry(state,identity,fabric,rights,profiles,origin,required_release_ref=CURRENT_RELEASE_REF if require_current_release else None)
    ingestion=ingest_mod.ContinuousProvenanceEngine(state,identity,fabric,evidence,rights,passports,origin.default_release_ref)
    packages=package_mod.IndustryImplementationPackageRegistry(); sdk=sdk_mod.EntityGlobalPassportSDK(profiles,passports,ingestion,packages)
    return identity,fabric,profiles,origin,passports,packages,sdk,origin_status
def read_json(path): return json.loads(pathlib.Path(path).read_text(encoding="utf-8-sig"))
def emit(value): print(json.dumps(value,indent=2,sort_keys=True))

def _btdu_for_controller(state,identity,controller_entity_id):
    controller=str(controller_entity_id); identity.load_manifest(controller)
    def verifier(record):
        try:
            body=dict(record["body"]); sig=dict(record["signature"])
            if body.get("scope")!="BTDU_WRITE" or body.get("actor_entity_id")!=controller: return False
            return identity.verify_signature(identity.load_manifest(controller),body,sig)
        except Exception: return False
    return btdu_mod.BlackmoreTechnologyDataUniverse(pathlib.Path(state)/"btdu"/controller,
        authorization_verifier=verifier,sovereign_entity_id=controller,
        protocol_entity_id=btdu_mod.ENTITY_PROTOCOL_ENTITY_ID,steward_entity_id=btdu_mod.BTG_STEWARD_ENTITY_ID)

def _btdu_receipt(identity,controller_entity_id,path,logical_path):
    raw=pathlib.Path(path).read_bytes(); nonce=hashlib.sha256(raw+b"|"+str(logical_path).encode()).hexdigest()
    body={"schema":"entity-btdu-authorization-v1","actor_entity_id":str(controller_entity_id),"scope":"BTDU_WRITE","nonce":nonce}
    return {"body":body,"signature":identity.sign(str(controller_entity_id),body)}

def cmd_init(a):
    identity,_,profiles,origin,_,_,_,origin_status=runtime(a.state,a.release_origin,require_current_release=True)
    aliases=list(a.alias or [])
    controller=identity.create(a.name,a.entity_type,aliases=aliases)["entity_id"]
    universe=_btdu_for_controller(a.state,identity,controller); btdu_root=universe.atomic.root_hash; universe.close()
    emit({"state":str(pathlib.Path(a.state).resolve()),"controller_entity_id":controller,
          "controller_entity_type":a.entity_type,"controller_aliases":aliases,
          "profiles":sorted(p["profile_ref"] for p in [profiles.get(ref) for ref in sorted(bundle_profile_refs())]),
          "protocol_origin":origin.passport_binding(origin.default_release_ref),
          "origin_installation":origin_status,"user_identity_is_independent":True,
          "user_asset_provenance_is_not_protocol_origin":True,
          "authority_must_be_configured_by_deployer":True,"btdu_namespace_initialized":True,"btdu_universe_root":btdu_root})

def bundle_profile_refs():
    return [p["profile_ref"] for p in read_json(ORIGIN_BUNDLE).get("canonical_profiles",[])]

def cmd_packages(a):
    _,_,_,_,_,packages,_,_=runtime(a.state,a.release_origin)
    emit({"packages":[packages.get(name) for name in packages.list_packages()]})

def cmd_plan(a):
    _,_,_,_,_,packages,sdk,_=runtime(a.state,a.release_origin)
    emit(sdk.package_plan(a.package,read_json(a.config),a.asset_kind))

def cmd_map(a):
    _,_,_,_,_,_,sdk,_=runtime(a.state,a.release_origin)
    emit(sdk.map_external(a.package,a.standard,read_json(a.input)))

def cmd_ingest(a):
    identity,_,profiles,origin,_,_,sdk,_=runtime(a.state,a.release_origin,require_current_release=True)
    try: profiles.get("entity-profile:global@1.0")
    except KeyError: raise SystemExit("state has no installed v3.4 profiles; run init first")
    logical=a.logical_path or pathlib.Path(a.file).name
    universe=_btdu_for_controller(a.state,identity,a.controller); receipt=_btdu_receipt(identity,a.controller,a.file,logical)
    btdu_obj=universe.ingest_file(a.file,receipt,logical_path=logical,source_entity_id=a.controller,
                                  controller_entity_id=a.controller,rights_holder_entity_id=a.controller,
                                  provenance_ref="entity-v3.4.3-ingest:"+logical)
    binding=universe.passport_binding(btdu_obj["object_ref"])
    out=sdk.ingest_package_file(a.file,a.controller,a.package,read_json(a.config),a.asset_kind,
                                logical_path=logical,version=a.version,btdu_binding=binding)
    out.update({"btdu_object_ref":btdu_obj["object_ref"],"btdu_binding":binding}); universe.close(); emit(out)

def cmd_verify(a):
    _,_,_,_,_,_,sdk,_=runtime(a.state,a.release_origin)
    emit(sdk.verify_passport(a.passport_id))

def cmd_origin(a):
    _,_,_,origin,_,_,_,status=runtime(a.state,a.release_origin)
    if a.release_ref:
        emit({"installation":status,"release":origin.passport_binding(a.release_ref)})
    else:
        emit({"installation":status,"default":origin.passport_binding(origin.default_release_ref)})
def parser():
    p=argparse.ArgumentParser(prog="entity-v3.4.3",description="ENTITY v3.4.3 Global Passport + BTDU deployment CLI")
    p.add_argument("--state",required=True,help="ENTITY state directory")
    p.add_argument("--release-origin",help="signed current-release origin attestation; required for v3.4.3 init/ingest unless bundled sidecar is present")
    sub=p.add_subparsers(dest="command",required=True)
    x=sub.add_parser("init"); x.add_argument("--name",required=True); x.add_argument("--entity-type",default="organization",choices=sorted(identity_mod.ENTITY_TYPES)); x.add_argument("--alias",action="append",default=[]); x.set_defaults(func=cmd_init)
    x=sub.add_parser("packages"); x.set_defaults(func=cmd_packages)
    x=sub.add_parser("plan"); x.add_argument("--package",required=True); x.add_argument("--config",required=True); x.add_argument("--asset-kind",required=True); x.set_defaults(func=cmd_plan)
    x=sub.add_parser("map"); x.add_argument("--package",required=True); x.add_argument("--standard",required=True); x.add_argument("--input",required=True); x.set_defaults(func=cmd_map)
    x=sub.add_parser("ingest"); x.add_argument("--controller",required=True); x.add_argument("--package",required=True); x.add_argument("--config",required=True)
    x.add_argument("--asset-kind",required=True); x.add_argument("--file",required=True); x.add_argument("--logical-path"); x.add_argument("--version",default="1.0"); x.set_defaults(func=cmd_ingest)
    x=sub.add_parser("verify"); x.add_argument("--passport-id",required=True); x.set_defaults(func=cmd_verify)
    x=sub.add_parser("origin"); x.add_argument("--release-ref"); x.set_defaults(func=cmd_origin)
    return p

def main(argv=None):
    args=parser().parse_args(argv); args.func(args); return 0

if __name__=="__main__": raise SystemExit(main())
