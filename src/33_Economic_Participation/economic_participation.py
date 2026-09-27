from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import hashlib, json, secrets, sqlite3, time

PROFILE_ID = 'ENTITY_ORIGINATOR_PARTICIPATION'
PROFILE_VERSION = '3.0.0'
SERVICE_TYPES = {'LISTING','EXECUTION','CLEARING','SETTLEMENT','MARKET_DATA','CERTIFICATION','MANAGED_INFRASTRUCTURE','API','INDEX_LICENCE','OTHER'}

def now_ms(): return int(time.time()*1000)
def rid(prefix): return prefix+'-'+secrets.token_hex(12)
def canon(v): return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,default=str).encode()
def sha(v): return hashlib.sha256(v if isinstance(v,(bytes,bytearray)) else canon(v)).hexdigest()
def require_sha256(v):
    s=str(v or '').lower()
    if len(s)!=64 or any(c not in '0123456789abcdef' for c in s): raise ValueError('SHA-256 hex required')
    return s

def require_bps(v,name):
    n=int(v)
    if n<0 or n>10000: raise ValueError(f'{name} must be 0..10000 basis points')
    return n

class EconomicParticipationProfile:
    '''Issuer-neutral treasury/originator participation profile for ENTITY/EEP.

    This profile creates no protocol tax and no token. Value comes from disclosed
    ownership of EEP rights units, contractual participation terms and service revenue.
    '''
    def __init__(self,root,identity):
        self.path=Path(root)/'entity_v3_economic_participation.sqlite'
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.identity=identity
        self._init()

    @contextmanager
    def _db(self):
        db=sqlite3.connect(self.path); db.row_factory=sqlite3.Row
        try:
            yield db; db.commit()
        except Exception:
            db.rollback(); raise
        finally:
            db.close()

    def _init(self):
        with self._db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS treasuries(
              treasury_id TEXT PRIMARY KEY, owner_entity_id TEXT NOT NULL,
              treasury_entity_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
              jurisdiction TEXT NOT NULL, policy_sha256 TEXT NOT NULL,
              status TEXT NOT NULL, created_at_ms INTEGER NOT NULL,
              signature_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS participation_policies(
              policy_id TEXT PRIMARY KEY, instrument_id TEXT NOT NULL, version INTEGER NOT NULL,
              originator_entity_id TEXT NOT NULL, treasury_id TEXT NOT NULL,
              total_units INTEGER NOT NULL, reserve_units INTEGER NOT NULL,
              primary_treasury_bps INTEGER NOT NULL, secondary_royalty_bps INTEGER NOT NULL,
              derivative_participation_bps INTEGER NOT NULL, currency TEXT NOT NULL,
              terms_sha256 TEXT NOT NULL, effective_at_ms INTEGER NOT NULL,
              status TEXT NOT NULL, created_at_ms INTEGER NOT NULL, signature_json TEXT NOT NULL,
              UNIQUE(instrument_id,version));
            CREATE TABLE IF NOT EXISTS reserve_allocations(
              allocation_id TEXT PRIMARY KEY, policy_id TEXT NOT NULL, instrument_id TEXT NOT NULL,
              originator_entity_id TEXT NOT NULL, treasury_entity_id TEXT NOT NULL,
              units INTEGER NOT NULL, created_at_ms INTEGER NOT NULL,
              originator_signature_json TEXT NOT NULL, treasury_signature_json TEXT NOT NULL,
              UNIQUE(policy_id));
            CREATE TABLE IF NOT EXISTS economic_events(
              event_id TEXT PRIMARY KEY, dedupe_key TEXT NOT NULL UNIQUE, event_type TEXT NOT NULL, policy_id TEXT,
              treasury_id TEXT NOT NULL, instrument_id TEXT, actor_entity_id TEXT NOT NULL,
              subject_ref TEXT NOT NULL, gross_amount_units INTEGER NOT NULL,
              currency TEXT NOT NULL, evidence_sha256 TEXT,
              details_json TEXT NOT NULL, created_at_ms INTEGER NOT NULL,
              signature_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS economic_event_evidence(
              event_id TEXT NOT NULL, evidence_sha256 TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL,
              PRIMARY KEY(event_id,evidence_sha256));
            CREATE TABLE IF NOT EXISTS obligations(
              obligation_id TEXT PRIMARY KEY, event_id TEXT NOT NULL,
              payer_entity_id TEXT NOT NULL, recipient_entity_id TEXT NOT NULL,
              amount_units INTEGER NOT NULL, currency TEXT NOT NULL,
              basis TEXT NOT NULL, bps INTEGER NOT NULL, status TEXT NOT NULL,
              settlement_ref TEXT, verifier_entity_id TEXT, verification_evidence_sha256 TEXT,
              external_verified INTEGER NOT NULL DEFAULT 0,
              created_at_ms INTEGER NOT NULL, settled_at_ms INTEGER);
            CREATE TABLE IF NOT EXISTS position_snapshots(
              snapshot_id TEXT PRIMARY KEY, treasury_id TEXT NOT NULL,
              snapshot_sha256 TEXT NOT NULL, snapshot_json TEXT NOT NULL,
              created_at_ms INTEGER NOT NULL, signature_json TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS settlement_verifiers(
              treasury_id TEXT NOT NULL, verifier_entity_id TEXT NOT NULL,
              status TEXT NOT NULL, created_at_ms INTEGER NOT NULL,
              signature_json TEXT NOT NULL, PRIMARY KEY(treasury_id,verifier_entity_id));
            CREATE UNIQUE INDEX IF NOT EXISTS idx_opr_reserve_once ON reserve_allocations(instrument_id);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_opr_obligation_event ON obligations(event_id);
            CREATE INDEX IF NOT EXISTS idx_opr_policy_instrument ON participation_policies(instrument_id,status);
            CREATE INDEX IF NOT EXISTS idx_opr_obligation_recipient ON obligations(recipient_entity_id,status,currency);
            ''')

    def create_treasury(self,owner_entity_id,treasury_entity_id,name,jurisdiction,policy_sha256):
        self.identity.load_manifest(owner_entity_id); self.identity.load_manifest(treasury_entity_id)
        body={'schema':'entity-v3-treasury-v1','profile':PROFILE_ID,'treasury_id':rid('treasury3'),
              'owner_entity_id':owner_entity_id,'treasury_entity_id':treasury_entity_id,
              'name':str(name)[:256],'jurisdiction':str(jurisdiction).upper(),
              'policy_sha256':require_sha256(policy_sha256),'status':'ACTIVE','created_at_ms':now_ms(),
              'protocol_tax_bps':0,'treasury_is_not_protocol_authority':True}
        sig=self.identity.sign(owner_entity_id,body)
        with self._db() as db:
            db.execute('INSERT INTO treasuries VALUES(?,?,?,?,?,?,?,?,?)',(
                body['treasury_id'],owner_entity_id,treasury_entity_id,body['name'],body['jurisdiction'],
                body['policy_sha256'],'ACTIVE',body['created_at_ms'],json.dumps(sig,sort_keys=True)))
        return dict(body,signature=sig)

    def _treasury(self,treasury_id):
        with self._db() as db:
            row=db.execute("SELECT * FROM treasuries WHERE treasury_id=? AND status='ACTIVE'",(treasury_id,)).fetchone()
        if not row: raise KeyError('active treasury not found')
        return row

    def authorize_settlement_verifier(self,treasury_id,owner_entity_id,verifier_entity_id):
        treasury=self._treasury(treasury_id)
        if treasury['owner_entity_id']!=owner_entity_id:
            raise PermissionError('treasury owner required')
        self.identity.load_manifest(verifier_entity_id)
        body={'schema':'entity-v3-settlement-verifier-authorization-v1','treasury_id':treasury_id,
              'owner_entity_id':owner_entity_id,'verifier_entity_id':verifier_entity_id,
              'status':'ACTIVE','created_at_ms':now_ms()}
        sig=self.identity.sign(owner_entity_id,body)
        with self._db() as db:
            db.execute('INSERT INTO settlement_verifiers VALUES(?,?,?,?,?) ON CONFLICT(treasury_id,verifier_entity_id) DO UPDATE SET status=excluded.status,created_at_ms=excluded.created_at_ms,signature_json=excluded.signature_json',
                       (treasury_id,verifier_entity_id,'ACTIVE',body['created_at_ms'],json.dumps(sig,sort_keys=True)))
        return dict(body,signature=sig)

    def revoke_settlement_verifier(self,treasury_id,owner_entity_id,verifier_entity_id):
        treasury=self._treasury(treasury_id)
        if treasury['owner_entity_id']!=owner_entity_id:
            raise PermissionError('treasury owner required')
        with self._db() as db:
            row=db.execute('SELECT 1 FROM settlement_verifiers WHERE treasury_id=? AND verifier_entity_id=?',(treasury_id,verifier_entity_id)).fetchone()
            if not row: raise KeyError('settlement verifier authorization not found')
            db.execute("UPDATE settlement_verifiers SET status='REVOKED' WHERE treasury_id=? AND verifier_entity_id=?",(treasury_id,verifier_entity_id))
        return {'treasury_id':treasury_id,'verifier_entity_id':verifier_entity_id,'status':'REVOKED'}

    def define_participation(self,originator_entity_id,treasury_id,instrument_id,total_units,reserve_units,currency,
                             *,primary_treasury_bps=0,secondary_royalty_bps=0,
                             derivative_participation_bps=0,version=1,effective_at_ms=None,terms=None):
        self.identity.load_manifest(originator_entity_id); treasury=self._treasury(treasury_id)
        if treasury['owner_entity_id']!=originator_entity_id:
            raise PermissionError('originator must own the selected treasury')
        total=int(total_units); reserve=int(reserve_units); version=int(version)
        if total<1 or reserve<0 or reserve>total: raise ValueError('invalid total/reserve units')
        if version<1: raise ValueError('positive policy version required')
        primary=require_bps(primary_treasury_bps,'primary_treasury_bps')
        secondary=require_bps(secondary_royalty_bps,'secondary_royalty_bps')
        derivative=require_bps(derivative_participation_bps,'derivative_participation_bps')
        with self._db() as db:
            latest=db.execute('SELECT version,effective_at_ms FROM participation_policies WHERE instrument_id=? ORDER BY version DESC LIMIT 1',(str(instrument_id),)).fetchone()
            allocation=db.execute('SELECT units FROM reserve_allocations WHERE instrument_id=?',(str(instrument_id),)).fetchone()
        if latest is not None and version<=int(latest['version']):
            raise ValueError('policy version must increase')
        created=now_ms()
        if effective_at_ms is None:
            effective=max(created,(int(latest['effective_at_ms'])+1) if latest is not None else created)
        else:
            effective=int(effective_at_ms)
            if effective<created: raise ValueError('participation policy cannot be retroactive')
            if latest is not None and effective<=int(latest['effective_at_ms']):
                raise ValueError('policy effective time must increase')
        if allocation is not None and reserve!=int(allocation['units']):
            raise ValueError('reserve units are immutable after allocation; use an explicit reserve-rebalance operation')
        term_doc=dict(terms or {})
        term_doc.update({'instrument_id':str(instrument_id),'total_units':total,'reserve_units':reserve,
                         'primary_treasury_bps':primary,'secondary_royalty_bps':secondary,
                         'derivative_participation_bps':derivative,'currency':str(currency).upper(),
                         'protocol_tax_bps':0})
        body={'schema':'entity-v3-originator-participation-policy-v1','profile':PROFILE_ID,
              'policy_id':rid('opr3'),'instrument_id':str(instrument_id),'version':version,
              'originator_entity_id':originator_entity_id,'treasury_id':treasury_id,
              'treasury_entity_id':treasury['treasury_entity_id'],'total_units':total,
              'reserve_units':reserve,'primary_treasury_bps':primary,
              'secondary_royalty_bps':secondary,'derivative_participation_bps':derivative,
              'currency':str(currency).upper(),'terms_sha256':sha(term_doc),
              'effective_at_ms':effective,'status':'ACTIVE','created_at_ms':created,
              'protocol_tax_bps':0,'terms_are_disclosed_and_issuer_signed':True,
              'no_retroactive_economic_rights':True}
        sig=self.identity.sign(originator_entity_id,body)
        with self._db() as db:
            db.execute("UPDATE participation_policies SET status='SUPERSEDED' WHERE instrument_id=? AND status='ACTIVE'",(str(instrument_id),))
            db.execute('INSERT INTO participation_policies VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                body['policy_id'],body['instrument_id'],version,originator_entity_id,treasury_id,total,reserve,
                primary,secondary,derivative,body['currency'],body['terms_sha256'],body['effective_at_ms'],
                'ACTIVE',body['created_at_ms'],json.dumps(sig,sort_keys=True)))
        return dict(body,signature=sig)

    def _active_policy(self,instrument_id,at_ms=None):
        at=int(at_ms or now_ms())
        with self._db() as db:
            row=db.execute("SELECT * FROM participation_policies WHERE instrument_id=? AND effective_at_ms<=? ORDER BY effective_at_ms DESC,version DESC LIMIT 1",(str(instrument_id),at)).fetchone()
        if not row: raise KeyError('effective participation policy not found')
        return row

    @contextmanager
    def _exchange_db(self,exchange):
        db=sqlite3.connect(exchange.path); db.row_factory=sqlite3.Row
        try:
            yield db; db.commit()
        except Exception:
            db.rollback(); raise
        finally:
            db.close()

    def allocate_eep_reserve(self,exchange,policy_id):
        with self._db() as db:
            policy=db.execute('SELECT * FROM participation_policies WHERE policy_id=?',(policy_id,)).fetchone()
            if not policy: raise KeyError('participation policy not found')
        current=self._active_policy(policy['instrument_id'],now_ms())
        if current['policy_id']!=policy_id:
            raise ValueError('reserve allocation requires the currently effective policy')
        treasury=self._treasury(policy['treasury_id']); originator=policy['originator_entity_id']; holder=treasury['treasury_entity_id']; units=int(policy['reserve_units'])
        if treasury['owner_entity_id']!=originator:
            raise PermissionError('policy originator must own treasury')
        self.identity.load_manifest(holder)
        body={'schema':'entity-v3-treasury-reserve-allocation-v1','allocation_id':rid('reserve3'),
              'policy_id':policy_id,'instrument_id':policy['instrument_id'],'originator_entity_id':originator,
              'treasury_entity_id':holder,'units':units,'created_at_ms':now_ms(),
              'eep_balance_transfer_enforced':holder!=originator,'protocol_tax_bps':0,
              'cross_store_atomic':True}
        origin_sig=self.identity.sign(originator,body); treasury_sig=self.identity.sign(holder,body)
        db=sqlite3.connect(self.path); db.row_factory=sqlite3.Row
        try:
            db.execute('ATTACH DATABASE ? AS eep',(str(exchange.path),))
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM main.reserve_allocations WHERE instrument_id=?',(policy['instrument_id'],)).fetchone():
                raise ValueError('reserve already allocated for instrument')
            effective=db.execute("SELECT * FROM main.participation_policies WHERE instrument_id=? AND effective_at_ms<=? ORDER BY effective_at_ms DESC,version DESC LIMIT 1",(policy['instrument_id'],now_ms())).fetchone()
            if not effective or effective['policy_id']!=policy_id:
                raise ValueError('reserve allocation requires the currently effective policy')
            inst=db.execute("SELECT * FROM eep.instruments WHERE instrument_id=? AND status='ACTIVE'",(policy['instrument_id'],)).fetchone()
            if not inst or inst['issuer']!=originator: raise PermissionError('policy originator must be EEP issuer')
            if int(inst['total_units'])!=int(policy['total_units']): raise ValueError('EEP supply differs from signed policy')
            if str(inst['settlement_currency']).upper()!=str(policy['currency']).upper(): raise ValueError('EEP currency differs from signed policy')
            if units:
                row=db.execute('SELECT units FROM eep.balances WHERE instrument_id=? AND holder=?',(policy['instrument_id'],originator)).fetchone()
                available=int(row['units']) if row else 0
                if available<units: raise PermissionError('issuer balance insufficient for reserve allocation')
                if holder!=originator:
                    db.execute('UPDATE eep.balances SET units=units-? WHERE instrument_id=? AND holder=?',(units,policy['instrument_id'],originator))
                    db.execute('INSERT INTO eep.balances(instrument_id,holder,units) VALUES(?,?,?) ON CONFLICT(instrument_id,holder) DO UPDATE SET units=units+excluded.units',(policy['instrument_id'],holder,units))
            db.execute('INSERT INTO main.reserve_allocations VALUES(?,?,?,?,?,?,?,?,?)',(
                body['allocation_id'],policy_id,policy['instrument_id'],originator,holder,units,body['created_at_ms'],
                json.dumps(origin_sig,sort_keys=True),json.dumps(treasury_sig,sort_keys=True)))
            db.commit()
        except Exception:
            db.rollback(); raise
        finally:
            db.close()
        return dict(body,originator_signature=origin_sig,treasury_signature=treasury_sig)

    def _event(self,event_type,policy,treasury,actor,subject_ref,gross,currency,details,evidence_sha256=None,dedupe_key=None):
        self.identity.load_manifest(actor)
        evidence=require_sha256(evidence_sha256) if evidence_sha256 else None
        key=str(dedupe_key or sha({'event_type':event_type,'policy_id':policy['policy_id'] if policy else None,
                                  'treasury_id':treasury['treasury_id'],'actor':actor,'subject_ref':str(subject_ref),
                                  'gross':int(gross),'currency':str(currency).upper(),'evidence_sha256':evidence}))
        body={'schema':'entity-v3-economic-event-v1','event_id':rid('econ3'),'dedupe_key':key,'event_type':event_type,
              'policy_id':policy['policy_id'] if policy else None,'treasury_id':treasury['treasury_id'],
              'instrument_id':policy['instrument_id'] if policy else None,'actor_entity_id':actor,
              'subject_ref':str(subject_ref),'gross_amount_units':int(gross),'currency':str(currency).upper(),
              'evidence_sha256':evidence,'details':dict(details or {}),'created_at_ms':now_ms(),
              'economic_event_is_evidence_not_market_value':True}
        sig=self.identity.sign(actor,body)
        try:
            with self._db() as db:
                db.execute('INSERT INTO economic_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                    body['event_id'],key,event_type,body['policy_id'],body['treasury_id'],body['instrument_id'],actor,
                    body['subject_ref'],body['gross_amount_units'],body['currency'],body['evidence_sha256'],
                    json.dumps(body['details'],sort_keys=True),body['created_at_ms'],json.dumps(sig,sort_keys=True)))
        except sqlite3.IntegrityError as exc:
            raise ValueError('duplicate/replayed economic event') from exc
        return dict(body,signature=sig)

    def _verify_eep_sell_order(self,order_row):
        body={'schema':'entity-eep-order-v1','order_id':order_row['order_id'],'venue_id':order_row['venue_id'],
              'instrument_id':order_row['instrument_id'],'participant':order_row['participant'],'side':order_row['side'],
              'quantity':int(order_row['quantity']),'limit_price':int(order_row['limit_price']),'tif':order_row['tif'],
              'nonce':order_row['nonce'],'created_at_ms':int(order_row['created_at_ms'])}
        manifest=self.identity.load_manifest(order_row['participant'])
        if not self.identity.verify_signature(manifest,body,json.loads(order_row['signature_json'])):
            raise PermissionError('EEP sell order signature invalid')
        return True

    def _obligation(self,event,payer,recipient,amount,currency,basis,bps):
        amount=max(0,int(amount)); bps=int(bps)
        if amount==0: return None
        oid=rid('obl3')
        with self._db() as db:
            db.execute('INSERT INTO obligations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                oid,event['event_id'],payer,recipient,amount,str(currency).upper(),basis,bps,'ACCRUED',
                None,None,None,0,now_ms(),None))
        return {'obligation_id':oid,'event_id':event['event_id'],'payer_entity_id':payer,
                'recipient_entity_id':recipient,'amount_units':amount,'currency':str(currency).upper(),
                'basis':basis,'bps':bps,'status':'ACCRUED','external_money_movement_verified':False}

    def _event_with_obligation(self,event_type,policy,treasury,actor,subject_ref,gross,currency,details,
                               payer,recipient,amount,basis,bps,evidence_sha256=None,dedupe_key=None):
        self.identity.load_manifest(actor)
        evidence=require_sha256(evidence_sha256) if evidence_sha256 else None
        key=str(dedupe_key or sha({'event_type':event_type,'policy_id':policy['policy_id'] if policy else None,
                                  'treasury_id':treasury['treasury_id'],'actor':actor,'subject_ref':str(subject_ref),
                                  'gross':int(gross),'currency':str(currency).upper(),'evidence_sha256':evidence}))
        created=now_ms()
        body={'schema':'entity-v3-economic-event-v1','event_id':rid('econ3'),'dedupe_key':key,'event_type':event_type,
              'policy_id':policy['policy_id'] if policy else None,'treasury_id':treasury['treasury_id'],
              'instrument_id':policy['instrument_id'] if policy else None,'actor_entity_id':actor,
              'subject_ref':str(subject_ref),'gross_amount_units':int(gross),'currency':str(currency).upper(),
              'evidence_sha256':evidence,'details':dict(details or {}),'created_at_ms':created,
              'economic_event_is_evidence_not_market_value':True}
        sig=self.identity.sign(actor,body)
        amount=max(0,int(amount)); bps=int(bps); obligation=None
        if amount:
            obligation={'obligation_id':rid('obl3'),'event_id':body['event_id'],'payer_entity_id':payer,
                        'recipient_entity_id':recipient,'amount_units':amount,'currency':str(currency).upper(),
                        'basis':basis,'bps':bps,'status':'ACCRUED','external_money_movement_verified':False}
        try:
            with self._db() as db:
                db.execute('INSERT INTO economic_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                    body['event_id'],key,event_type,body['policy_id'],body['treasury_id'],body['instrument_id'],actor,
                    body['subject_ref'],body['gross_amount_units'],body['currency'],body['evidence_sha256'],
                    json.dumps(body['details'],sort_keys=True),body['created_at_ms'],json.dumps(sig,sort_keys=True)))
                if obligation:
                    db.execute('INSERT INTO obligations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(
                        obligation['obligation_id'],body['event_id'],payer,recipient,amount,str(currency).upper(),basis,bps,
                        'ACCRUED',None,None,None,0,created,None))
        except sqlite3.IntegrityError as exc:
            raise ValueError('duplicate/replayed economic event or obligation') from exc
        return dict(body,signature=sig),obligation

    def capture_settled_eep_trade(self,exchange,trade_id):
        with self._exchange_db(exchange) as ex:
            trade=ex.execute("SELECT * FROM trades WHERE trade_id=? AND status='SETTLED'",(str(trade_id),)).fetchone()
            clearing=ex.execute("SELECT * FROM clearing WHERE trade_id=? AND status='SETTLED'",(str(trade_id),)).fetchone()
            if not trade or not clearing: raise KeyError('settled EEP trade required')
            inst=ex.execute('SELECT * FROM instruments WHERE instrument_id=?',(trade['instrument_id'],)).fetchone()
            sell_order=ex.execute('SELECT * FROM orders WHERE order_id=?',(trade['sell_order_id'],)).fetchone()
        if not sell_order or sell_order['participant']!=trade['seller']: raise PermissionError('settled trade/sell order mismatch')
        self._verify_eep_sell_order(sell_order)
        policy=self._active_policy(trade['instrument_id'],trade['created_at_ms']); treasury=self._treasury(policy['treasury_id'])
        if inst['issuer']!=policy['originator_entity_id']: raise PermissionError('instrument issuer/policy originator mismatch')
        is_primary=trade['seller']==inst['issuer']; event_type='PRIMARY_RIGHTS_SALE' if is_primary else 'SECONDARY_RIGHTS_SALE'
        gross=int(clearing['amount_units']); bps=int(policy['primary_treasury_bps'] if is_primary else policy['secondary_royalty_bps'])
        event,obligation=self._event_with_obligation(
            event_type,policy,treasury,policy['originator_entity_id'],trade_id,gross,clearing['currency'],{
                'buyer':trade['buyer'],'seller':trade['seller'],'quantity':int(trade['quantity']),'price':int(trade['price']),
                'source_payment_ref':clearing['payment_ref'],'source_external_verified':bool(clearing['external_verified']),
                'sell_order_signature_verified':True,'sell_order_id':sell_order['order_id'],
                'participation_is_allocation_within_gross':True,'atomic_event_obligation':True},
            trade['seller'],treasury['treasury_entity_id'],gross*bps//10000,
            'PRIMARY_TREASURY_ALLOCATION' if is_primary else 'SECONDARY_ORIGINATOR_ROYALTY',bps,
            dedupe_key=f"EEP_TRADE:{trade_id}:{policy['policy_id']}")
        return {'event':event,'obligation':obligation,'trade_class':'PRIMARY' if is_primary else 'SECONDARY',
                'gross_amount_units':gross,'protocol_tax_bps':0}

    def record_derivative_revenue(self,policy_id,payer_entity_id,derivative_ref,gross_amount_units,currency,evidence_sha256,*,occurred_at_ms=None,occurrence_ref=None):
        with self._db() as db:
            policy=db.execute('SELECT * FROM participation_policies WHERE policy_id=?',(policy_id,)).fetchone()
        if not policy: raise KeyError('participation policy not found')
        occurred=int(occurred_at_ms or now_ms())
        if occurred>now_ms(): raise ValueError('derivative revenue event cannot be future-dated')
        effective=self._active_policy(policy['instrument_id'],occurred)
        if effective['policy_id']!=policy_id:
            raise ValueError('selected participation policy was not effective at derivative event time')
        currency=str(currency).upper()
        if currency!=str(policy['currency']).upper():
            raise ValueError('derivative revenue currency differs from participation policy')
        evidence=require_sha256(evidence_sha256)
        treasury=self._treasury(policy['treasury_id']); bps=int(policy['derivative_participation_bps']); gross=max(0,int(gross_amount_units))
        authoritative_occurrence_ref=str(occurrence_ref) if occurrence_ref is not None else f"legacy-ms:{occurred}"
        if not authoritative_occurrence_ref:
            raise ValueError('authoritative occurrence reference must not be empty')
        occurrence_identity=sha({
            'policy_id':policy_id,
            'payer_entity_id':payer_entity_id,
            'derivative_ref':str(derivative_ref),
            'occurrence_ref':authoritative_occurrence_ref,
        })
        dedupe_key=f"DERIVATIVE_OCCURRENCE:{policy_id}:{occurrence_identity}"
        with self._db() as db:
            existing=db.execute('SELECT * FROM economic_events WHERE dedupe_key=?',(dedupe_key,)).fetchone()
            if existing is not None:
                details=json.loads(existing['details_json'])
                if (existing['event_type']!='DERIVATIVE_COMMERCIAL_REVENUE' or
                    existing['policy_id']!=policy_id or
                    existing['actor_entity_id']!=payer_entity_id or
                    existing['subject_ref']!=str(derivative_ref) or
                    int(existing['gross_amount_units'])!=gross or
                    existing['currency']!=currency or
                    int(details.get('occurred_at_ms',-1))!=occurred):
                    raise ValueError('authoritative occurrence reference conflicts with existing economic occurrence')
                already_attached=(
                    existing['evidence_sha256']==evidence or
                    db.execute(
                        'SELECT 1 FROM economic_event_evidence WHERE event_id=? AND evidence_sha256=?',
                        (existing['event_id'],evidence)
                    ).fetchone() is not None
                )
                if already_attached:
                    raise ValueError('duplicate/replayed economic event')
                db.execute(
                    'INSERT INTO economic_event_evidence(event_id,evidence_sha256,created_at_ms) VALUES(?,?,?)',
                    (existing['event_id'],evidence,now_ms())
                )
                obligation=db.execute('SELECT * FROM obligations WHERE event_id=?',(existing['event_id'],)).fetchone()
                event={
                    'schema':'entity-v3-economic-event-v1','event_id':existing['event_id'],'dedupe_key':existing['dedupe_key'],
                    'event_type':existing['event_type'],'policy_id':existing['policy_id'],'treasury_id':existing['treasury_id'],
                    'instrument_id':existing['instrument_id'],'actor_entity_id':existing['actor_entity_id'],
                    'subject_ref':existing['subject_ref'],'gross_amount_units':int(existing['gross_amount_units']),
                    'currency':existing['currency'],'evidence_sha256':existing['evidence_sha256'],'details':details,
                    'created_at_ms':int(existing['created_at_ms']),'economic_event_is_evidence_not_market_value':True,
                    'signature':json.loads(existing['signature_json']),
                }
                obligation_body=None if obligation is None else {
                    'obligation_id':obligation['obligation_id'],'event_id':obligation['event_id'],
                    'payer_entity_id':obligation['payer_entity_id'],'recipient_entity_id':obligation['recipient_entity_id'],
                    'amount_units':int(obligation['amount_units']),'currency':obligation['currency'],
                    'basis':obligation['basis'],'bps':int(obligation['bps']),'status':obligation['status'],
                    'external_money_movement_verified':bool(obligation['external_verified']),
                }
                return {'event':event,'obligation':obligation_body,'protocol_tax_bps':0}
        event,obligation=self._event_with_obligation(
            'DERIVATIVE_COMMERCIAL_REVENUE',policy,treasury,payer_entity_id,derivative_ref,gross,currency,
            {'revenue_amount_asserted_by_payer':True,'methodology':'CONTRACTUAL_BPS','occurred_at_ms':occurred,
             'policy_bound_at_event_time':True,'atomic_event_obligation':True,
             'occurrence_ref':authoritative_occurrence_ref,'occurrence_identity':occurrence_identity,
             'occurrence_identity_is_evidence_independent':True},
            payer_entity_id,treasury['treasury_entity_id'],gross*bps//10000,'DERIVATIVE_PARTICIPATION',bps,
            evidence,dedupe_key=dedupe_key)
        with self._db() as db:
            db.execute('INSERT OR IGNORE INTO economic_event_evidence(event_id,evidence_sha256,created_at_ms) VALUES(?,?,?)',
                       (event['event_id'],evidence,now_ms()))
        return {'event':event,'obligation':obligation,'protocol_tax_bps':0}

    def record_service_revenue(self,treasury_id,payer_entity_id,service_type,amount_units,currency,basis_ref,evidence_sha256=None):
        service_type=str(service_type).upper()
        if service_type not in SERVICE_TYPES: raise ValueError('unsupported service type')
        treasury=self._treasury(treasury_id); amount=max(0,int(amount_units)); currency=str(currency).upper()
        self.identity.load_manifest(payer_entity_id)
        provider=treasury['owner_entity_id']
        event,obligation=self._event_with_obligation(
            'PROVIDER_SERVICE_REVENUE',None,treasury,provider,basis_ref,amount,currency,
            {'service_type':service_type,'provider_entity_id':provider,'payer_entity_id':payer_entity_id,
             'provider_identity_not_protocol_privilege':True,'provider_asserted_receivable':True,
             'payer_signature_not_required_to_record_provider_receivable':True,'atomic_event_obligation':True},
            payer_entity_id,treasury['treasury_entity_id'],amount,'SERVICE_REVENUE',10000,
            evidence_sha256,dedupe_key=f"SERVICE:{treasury_id}:{service_type}:{basis_ref}")
        return {'event':event,'obligation':obligation,'protocol_tax_bps':0}

    def settle_obligation(self,obligation_id,verifier_entity_id,settlement_ref,*,external_verified=False,evidence_sha256=None):
        if external_verified and not evidence_sha256: raise ValueError('verification evidence required for external verification')
        evidence=require_sha256(evidence_sha256) if evidence_sha256 else None
        with self._db() as db:
            row=db.execute("SELECT * FROM obligations WHERE obligation_id=? AND status='ACCRUED'",(obligation_id,)).fetchone()
            if not row: raise KeyError('accrued obligation not found')
            event=db.execute('SELECT * FROM economic_events WHERE event_id=?',(row['event_id'],)).fetchone()
            if not event: raise KeyError('economic event missing')
            treasury=db.execute("SELECT * FROM treasuries WHERE treasury_id=? AND status='ACTIVE'",(event['treasury_id'],)).fetchone()
            if not treasury: raise KeyError('active treasury missing')
            auth=db.execute("SELECT status FROM settlement_verifiers WHERE treasury_id=? AND verifier_entity_id=?",(event['treasury_id'],verifier_entity_id)).fetchone()
        if verifier_entity_id==row['payer_entity_id']:
            authority='PAYER_ATTESTATION'
        elif verifier_entity_id==treasury['owner_entity_id']:
            authority='TREASURY_OWNER_ATTESTATION'
        elif verifier_entity_id==treasury['treasury_entity_id']:
            authority='TREASURY_ENTITY_ATTESTATION'
        elif auth and auth['status']=='ACTIVE':
            authority='AUTHORIZED_SETTLEMENT_VERIFIER'
        else:
            raise PermissionError('verifier is not authorized for this treasury obligation')
        self.identity.load_manifest(verifier_entity_id)
        verification={'schema':'entity-v3-obligation-settlement-attestation-v1','obligation_id':obligation_id,
                      'verifier_entity_id':verifier_entity_id,'verifier_authority_basis':authority,
                      'settlement_ref':str(settlement_ref),'external_verified':bool(external_verified),
                      'evidence_sha256':evidence,'created_at_ms':now_ms(),
                      'verification_is_attestation_not_absolute_truth':True}
        sig=self.identity.sign(verifier_entity_id,verification)
        with self._db() as db:
            db.execute("UPDATE obligations SET status='SETTLED',settlement_ref=?,verifier_entity_id=?,verification_evidence_sha256=?,external_verified=?,settled_at_ms=? WHERE obligation_id=?",
                       (str(settlement_ref),verifier_entity_id,evidence,int(bool(external_verified)),verification['created_at_ms'],obligation_id))
        return dict(verification,signature=sig,status='SETTLED')

    def position(self,treasury_id,exchange=None):
        treasury=self._treasury(treasury_id)
        with self._db() as db:
            instruments=[r['instrument_id'] for r in db.execute('SELECT DISTINCT instrument_id FROM participation_policies WHERE treasury_id=? ORDER BY instrument_id',(treasury_id,)).fetchall()]
            obs=db.execute("SELECT currency,status,SUM(amount_units) amount FROM obligations WHERE recipient_entity_id=? GROUP BY currency,status ORDER BY currency,status",(treasury['treasury_entity_id'],)).fetchall()
        policies=[]
        for instrument_id in instruments:
            try: policies.append(self._active_policy(instrument_id,now_ms()))
            except KeyError: pass
        monetary={}
        for r in obs: monetary.setdefault(r['currency'],{})[r['status']]=int(r['amount'] or 0)
        reserves=[]
        if exchange is not None:
            for p in policies:
                with self._exchange_db(exchange) as ex:
                    row=ex.execute('SELECT units FROM balances WHERE instrument_id=? AND holder=?',(p['instrument_id'],treasury['treasury_entity_id'])).fetchone()
                reserves.append({'instrument_id':p['instrument_id'],'policy_version':int(p['version']),
                                 'signed_reserve_units':int(p['reserve_units']),'current_eep_units':int(row['units']) if row else 0})
        return {'schema':'entity-v3-treasury-position-v1','treasury_id':treasury_id,
                'owner_entity_id':treasury['owner_entity_id'],'treasury_entity_id':treasury['treasury_entity_id'],
                'monetary_obligations':monetary,'reserve_positions':reserves,
                'protocol_tax_bps':0,'token_balance':None,'value_sources':['RIGHTS_RESERVES','ORIGINATOR_PARTICIPATION','SERVICE_REVENUE'],
                'position_is_auditable_record_not_a_market_valuation':True}

    def reconcile_eep_trades(self,exchange,instrument_id=None):
        with self._exchange_db(exchange) as ex:
            if instrument_id is None:
                trades=ex.execute("SELECT * FROM trades WHERE status='SETTLED' ORDER BY created_at_ms,trade_id").fetchall()
            else:
                trades=ex.execute("SELECT * FROM trades WHERE status='SETTLED' AND instrument_id=? ORDER BY created_at_ms,trade_id",(str(instrument_id),)).fetchall()
            clearing={r['trade_id']:r for r in ex.execute("SELECT * FROM clearing WHERE status='SETTLED'").fetchall()}
            instruments={r['instrument_id']:r for r in ex.execute('SELECT * FROM instruments').fetchall()}
        missing=[]; captured=[]; out_of_scope=[]; mismatches=[]; missing_obligations=[]; obligation_mismatches=[]
        for trade in trades:
            try: policy=self._active_policy(trade['instrument_id'],trade['created_at_ms'])
            except KeyError:
                out_of_scope.append(trade['trade_id']); continue
            key=f"EEP_TRADE:{trade['trade_id']}:{policy['policy_id']}"
            clear=clearing.get(trade['trade_id']); inst=instruments.get(trade['instrument_id'])
            with self._db() as db:
                event=db.execute('SELECT * FROM economic_events WHERE dedupe_key=?',(key,)).fetchone()
                obligations=db.execute('SELECT * FROM obligations WHERE event_id=? ORDER BY obligation_id',(event['event_id'],)).fetchall() if event else []
            if not event:
                missing.append(trade['trade_id']); continue
            captured.append(trade['trade_id'])
            if (not clear or not inst or event['policy_id']!=policy['policy_id'] or
                int(event['gross_amount_units'])!=int(clear['amount_units']) or event['currency']!=clear['currency']):
                mismatches.append(trade['trade_id']); continue
            is_primary=trade['seller']==inst['issuer']
            bps=int(policy['primary_treasury_bps'] if is_primary else policy['secondary_royalty_bps'])
            basis='PRIMARY_TREASURY_ALLOCATION' if is_primary else 'SECONDARY_ORIGINATOR_ROYALTY'
            expected_amount=int(clear['amount_units'])*bps//10000
            treasury=self._treasury(policy['treasury_id'])
            if expected_amount==0:
                if obligations: obligation_mismatches.append(trade['trade_id'])
                continue
            if len(obligations)!=1:
                missing_obligations.append(trade['trade_id']); continue
            obligation=obligations[0]
            if (obligation['payer_entity_id']!=trade['seller'] or
                obligation['recipient_entity_id']!=treasury['treasury_entity_id'] or
                int(obligation['amount_units'])!=expected_amount or obligation['currency']!=clear['currency'] or
                obligation['basis']!=basis or int(obligation['bps'])!=bps):
                obligation_mismatches.append(trade['trade_id'])
        complete=not missing and not mismatches and not missing_obligations and not obligation_mismatches
        return {'schema':'entity-v3-eopp-reconciliation-v1','scanned_settled_trades':len(trades),
                'in_scope_trades':len(missing)+len(captured),'captured_trade_ids':captured,
                'missing_trade_ids':missing,'out_of_scope_trade_ids':out_of_scope,'mismatched_trade_ids':mismatches,
                'missing_obligation_trade_ids':missing_obligations,
                'mismatched_obligation_trade_ids':obligation_mismatches,
                'complete':complete,'event_and_obligation_reconciled':True,'protocol_tax_bps':0}

    def indicative_mark(self,treasury_id,exchange,price_source='LAST'):
        price_source=str(price_source).upper()
        if price_source not in {'LAST','BID','ASK'}: raise ValueError('unsupported price source')
        pos=self.position(treasury_id,exchange); marks=[]
        for r in pos['reserve_positions']:
            with self._exchange_db(exchange) as ex:
                if price_source=='LAST': row=ex.execute('SELECT price FROM trades WHERE instrument_id=? ORDER BY created_at_ms DESC LIMIT 1',(r['instrument_id'],)).fetchone()
                elif price_source=='BID': row=ex.execute("SELECT MAX(limit_price) price FROM orders WHERE instrument_id=? AND side='BUY' AND status IN ('OPEN','PARTIAL')",(r['instrument_id'],)).fetchone()
                else: row=ex.execute("SELECT MIN(limit_price) price FROM orders WHERE instrument_id=? AND side='SELL' AND status IN ('OPEN','PARTIAL')",(r['instrument_id'],)).fetchone()
                inst=ex.execute('SELECT settlement_currency FROM instruments WHERE instrument_id=?',(r['instrument_id'],)).fetchone()
            price=int(row['price']) if row and row['price'] is not None else None
            marks.append({'instrument_id':r['instrument_id'],'units':r['current_eep_units'],'price_source':price_source,
                          'observed_unit_price':price,'currency':inst['settlement_currency'] if inst else None,
                          'indicative_amount_units':r['current_eep_units']*price if price is not None else None})
        return {'schema':'entity-v3-treasury-indicative-mark-v1','treasury_id':treasury_id,'marks':marks,
                'indicative_only':True,'not_accounting_fair_value':True,'not_protocol_generated_value':True}

    def seal_snapshot(self,treasury_id,owner_entity_id,exchange=None):
        treasury=self._treasury(treasury_id)
        if treasury['owner_entity_id']!=owner_entity_id: raise PermissionError('treasury owner required')
        position=self.position(treasury_id,exchange); body={'schema':'entity-v3-treasury-snapshot-v1','snapshot_id':rid('treasnap3'),
            'treasury_id':treasury_id,'position_sha256':sha(position),'created_at_ms':now_ms(),'protocol_tax_bps':0}
        sig=self.identity.sign(owner_entity_id,body)
        with self._db() as db:
            db.execute('INSERT INTO position_snapshots VALUES(?,?,?,?,?,?)',(body['snapshot_id'],treasury_id,body['position_sha256'],json.dumps(position,sort_keys=True),body['created_at_ms'],json.dumps(sig,sort_keys=True)))
        return dict(body,position=position,signature=sig)

    def status(self):
        with self._db() as db:
            counts={t:int(db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]) for t in ('treasuries','participation_policies','reserve_allocations','economic_events','obligations','position_snapshots','settlement_verifiers')}
        return {'schema':'entity-v3-economic-participation-status-v1','profile':PROFILE_ID,'version':PROFILE_VERSION,
                'protocol_tax_bps':0,'cryptocurrency_required':False,'issuer_neutral':True,
                'treasury_reserves':True,'primary_participation':True,'secondary_royalties':True,
                'derivative_participation':True,'service_revenue':True,'auditable_positions':True,
                'indicative_market_marks':True,'settlement_verifier_authorization':True,
                'trade_capture_reconciliation':True,'historical_policy_resolution':True,'counts':counts}
