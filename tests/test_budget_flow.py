import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from fastapi.testclient import TestClient
from src.main import app,DB
def make(c):return c.post('/api/trips',json={'origin':'Bengaluru','destination':'Jaipur','depart_date':'2026-10-10','return_date':'2026-10-13','travellers':2,'budget_paise':3000000,'language':'Hindi'}).json()['trip']['id']
def test_hard_proof_budget_guard():
 if DB.exists():DB.unlink()
 with TestClient(app)as c:
  tid=make(c);assert c.post(f'/api/trips/{tid}/flight',json={'item_id':'FL-ECO'}).status_code==200
  blocked=c.post(f'/api/trips/{tid}/package',json={'item_id':'PKG-JAI-ROY'});assert blocked.status_code==409
  nid=blocked.json()['detail']['negotiation_id'];assert c.post(f'/api/trips/{tid}/confirm').status_code==409
  assert c.post(f'/api/trips/{tid}/negotiate/{nid}',json={'action':'drop_item'}).status_code==200
  assert c.post(f'/api/trips/{tid}/package',json={'item_id':'PKG-JAI-ESS'}).status_code==200
  assert c.post(f'/api/trips/{tid}/skip-guide').status_code==200
  assert c.post(f'/api/trips/{tid}/confirm').json()['status']=='confirmed'
def test_boundaries():
 if DB.exists():DB.unlink()
 with TestClient(app)as c:assert c.post('/api/trips',json={'origin':'Jaipur','destination':'Jaipur','depart_date':'2026-10-10','return_date':'2026-10-09','travellers':0,'budget_paise':1}).status_code==422
def test_raise_cap_advances_the_original_selection():
 if DB.exists():DB.unlink()
 with TestClient(app)as c:
  tid=make(c);c.post(f'/api/trips/{tid}/flight',json={'item_id':'FL-ECO'})
  b=c.post(f'/api/trips/{tid}/package',json={'item_id':'PKG-JAI-ROY'}).json()['detail']
  assert c.post(f"/api/trips/{tid}/negotiate/{b['negotiation_id']}",json={'action':'raise_cap'}).json()['status']=='select_guide'
