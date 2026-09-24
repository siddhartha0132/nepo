"""Offline, budget-honest PackagePro API. Prices are integer INR paise."""
import json, os, sqlite3, uuid
from contextlib import closing
from datetime import date
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data-model'; DB=ROOT/os.getenv('DATABASE_URL','sqlite:///./packagepro.sqlite3').replace('sqlite:///','')
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def boot():
 DB.parent.mkdir(parents=True,exist_ok=True)
 with closing(conn()) as c:
  c.executescript((DATA/'schema.sql').read_text())
  if not c.execute('select count(*) from packages').fetchone()[0]:
   for table, rows in json.loads((DATA/'seed/demo_data.json').read_text()).items():
    for row in rows: c.execute(f"insert into {table} ({','.join(row)}) values ({','.join('?'*len(row))})",tuple(row.values()))
   c.commit()
app=FastAPI(title='RNG Gods — PackagePro'); app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5174').split(','),allow_methods=['*'],allow_headers=['*'])
@app.on_event('startup')
def startup(): boot()
class TripIn(BaseModel):
 origin:str=Field(min_length=2); destination:str=Field(min_length=2); depart_date:date; return_date:date; travellers:int=Field(ge=1,le=8); budget_paise:int=Field(ge=500000,le=50000000); language:str='English'
 @model_validator(mode='after')
 def valid(self):
  if self.origin.casefold()==self.destination.casefold(): raise ValueError('Origin and destination must differ')
  if self.return_date<=self.depart_date: raise ValueError('Return date must be after departure date')
  return self
class Choice(BaseModel): item_id:str
class Resolve(BaseModel): action:str
def get(c,tid):
 r=c.execute('select * from trips where id=?',(tid,)).fetchone()
 if not r: raise HTTPException(404,'Trip not found')
 return r
def total(c,tid): return c.execute('select coalesce(sum(price_paise),0) from trip_items where trip_id=?',(tid,)).fetchone()[0]
def view(c,t):
 n=c.execute('select * from negotiations where trip_id=? and resolved=0',(t['id'],)).fetchone()
 return dict(t)|{'total_paise':total(c,t['id']),'items':[dict(x) for x in c.execute('select * from trip_items where trip_id=?',(t['id'],))],'pending_negotiation':dict(n) if n else None}
def guard(c,t,kind,label,price,ref):
 over=total(c,t['id'])+price-t['budget_paise']
 if over>0:
  nid=str(uuid.uuid4()); c.execute('insert into negotiations values(?,?,?,?,?,?,0)',(nid,t['id'],kind,label,price,over)); c.commit()
  raise HTTPException(409,{'code':'BUDGET_EXCEEDED','negotiation_id':nid,'item_label':label,'overage_paise':over,'moves':['raise_cap','drop_item','swap_cheaper']})
 c.execute('insert or replace into trip_items values(?,?,?,?,?)',(t['id'],kind,ref,label,price)); c.commit()
@app.get('/api/health')
def health(): return {'ok':True}
@app.post('/api/trips')
def create(p:TripIn):
 with closing(conn()) as c:
  tid=str(uuid.uuid4()); c.execute('insert into trips values(?,?,?,?,?,?,?,?,?)',(tid,p.origin,p.destination,str(p.depart_date),str(p.return_date),p.travellers,p.budget_paise,p.language,'select_flight')); c.commit(); t=get(c,tid)
  return {'trip':view(c,t),'flights':[{'id':'FL-ECO','display_name':'IndiGo Economy','price_paise':720000},{'id':'FL-FLEX','display_name':'Vistara Flex','price_paise':980000}],'packages':[dict(x) for x in c.execute('select * from packages where city=?',(p.destination,))]}
@app.post('/api/trips/{tid}/flight')
def flight(tid:str,p:Choice):
 opts={'FL-ECO':('IndiGo Economy',720000),'FL-FLEX':('Vistara Flex',980000)}
 if p.item_id not in opts: raise HTTPException(404,'Flight not found')
 with closing(conn()) as c:
  t=get(c,tid); guard(c,t,'flight',*opts[p.item_id],p.item_id); c.execute("update trips set status='select_package' where id=?",(tid,)); c.commit(); return view(c,get(c,tid))
@app.post('/api/trips/{tid}/package')
def package(tid:str,p:Choice):
 with closing(conn()) as c:
  t=get(c,tid); x=c.execute('select * from packages where id=? and city=?',(p.item_id,t['destination'])).fetchone()
  if not x: raise HTTPException(404,'Package not found')
  guard(c,t,'package',x['title'],x['price_paise'],x['id']); c.execute("update trips set status='select_guide' where id=?",(tid,)); c.commit(); return view(c,get(c,tid))
@app.get('/api/trips/{tid}/guides')
def guides(tid:str):
 with closing(conn()) as c:
  t=get(c,tid); return [dict(x)|{'language_match':x['language']==t['language']} for x in c.execute('select * from guides where city=? order by (language=?) desc,rating desc',(t['destination'],t['language']))]
@app.post('/api/trips/{tid}/guide')
def guide(tid:str,p:Choice):
 with closing(conn()) as c:
  t=get(c,tid); x=c.execute('select * from guides where id=? and city=?',(p.item_id,t['destination'])).fetchone()
  if not x: raise HTTPException(404,'Guide not found')
  guard(c,t,'guide',x['display_name'],x['price_paise'],x['id']); c.execute("update trips set status='review' where id=?",(tid,)); c.commit(); return view(c,get(c,tid))
@app.post('/api/trips/{tid}/skip-guide')
def skip(tid:str):
 with closing(conn()) as c: get(c,tid); c.execute("update trips set status='review' where id=?",(tid,)); c.commit(); return view(c,get(c,tid))
@app.post('/api/trips/{tid}/negotiate/{nid}')
def negotiate(tid:str,nid:str,p:Resolve):
 with closing(conn()) as c:
  t=get(c,tid); n=c.execute('select * from negotiations where id=? and trip_id=? and resolved=0',(nid,tid)).fetchone()
  if not n: raise HTTPException(404,'Pending negotiation not found')
  if p.action=='raise_cap':
   c.execute('update trips set budget_paise=budget_paise+? where id=?',(n['overage_paise'],tid)); guard(c,get(c,tid),n['kind'],n['item_label'],n['proposed_price_paise'],'negotiated')
   c.execute('update trips set status=? where id=?',({'flight':'select_package','package':'select_guide','guide':'review'}[n['kind']],tid))
  elif p.action!='drop_item': raise HTTPException(422,'Action must be raise_cap or drop_item')
  c.execute('update negotiations set resolved=1 where id=?',(nid,)); c.commit(); return view(c,get(c,tid))
@app.post('/api/trips/{tid}/confirm')
def confirm(tid:str):
 with closing(conn()) as c:
  t=get(c,tid)
  if c.execute('select 1 from negotiations where trip_id=? and resolved=0',(tid,)).fetchone(): raise HTTPException(409,'Resolve pending budget negotiation')
  if t['status']!='review': raise HTTPException(409,'Complete booking steps first')
  c.execute("update trips set status='confirmed' where id=?",(tid,)); c.commit(); return view(c,get(c,tid))
@app.post('/api/assistant/summary')
def summary(body:dict):
 with closing(conn()) as c:
  t=get(c,body['trip_id']); p=c.execute("select label from trip_items where trip_id=? and kind='package'",(t['id'],)).fetchone()
  if not p: raise HTTPException(409,'Choose a package first')
  return {'grounded':True,'summary':f"Your selected itinerary is {p[0]} in {t['destination']}."}
