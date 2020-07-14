from app import db
from app.models import Chemical, Exposure
import json, os
import pandas as pd

session = db.session


#add molecular weight information to chemicals
with open(os.path.join(".", "data", "chemicals_info.json"), 'r') as f:
    ch_info = json.load(f)

add_maps = []

for cid, cas, name in session.query(Chemical.id, Chemical.cas_number,
                                    Chemical.name):
    if cas != "No CAS":
        idx = [x['cas_number'] == cas for x in ch_info]
    else:
        idx = [x['name'] == name for x in ch_info]
    idx_num = [i for i, x in enumerate(idx) if x]
    print(cas)
    print(name)
    print(idx_num)
    if len(idx_num) == 0:
        print("match")
        continue
    elif len(idx_num) > 1:
        print("no unique match")

    print("---")
    idx_num = idx_num[0]

    if 'molecular_weight' not in ch_info[idx_num]:
        continue

    info = {
        "id": cid,
        "molecular_weight": ch_info[idx_num]['molecular_weight']
    }
    add_maps.append(info)

session.bulk_update_mappings(Chemical, add_maps)

session.commit()


# add year information to exposure
with open(os.path.join(".", "data", "year_info.csv"), 'r') as f:
    year_info = pd.read_csv(f)

import re

#handle cases of malformed input
ml = re.search(
    '[\d\.]+(?=mL)',
    'GUT_jen_24_0024h_AB_m1_FBS00_002mL_nn_in_no_D_16251-77-7').group(0)
short_id = re.sub('_[\d\.]+mL', '',
                  'GUT_jen_24_0024h_AB_m1_FBS00_002mL_nn_in_no_D_16251-77-7')
short_ids = [re.sub('_[\d\.]+mL', '', x) for x in year_info.ID]
short_ids = [re.sub("024hh", "0024h", x) for x in short_ids]
year_info_dict = dict(zip(short_ids, year_info.year))

t1 = []
for eid, sid in session.query(Exposure.id, Exposure.id_string):
    t1.append(sid)

year_maps = []
for eid, sid in session.query(Exposure.id, Exposure.id_string):
    if sid == 'GIL_gay_24_024h_AB_m1_FBS00_002mL_nn_in_no_D_95-76-1':
        print("found")
    if sid in year_info_dict:
        yinfo = {"id": eid, "year": year_info_dict[sid]}
        year_maps.append(yinfo)

year_maps
session.bulk_update_mappings(Exposure, year_maps)

session.commit()
