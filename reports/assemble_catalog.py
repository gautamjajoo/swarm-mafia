"""Assemble the private, server-only curated reports from reviewed source packets."""
import json
from pathlib import Path
files=['reports/investigator/terrarium-platform.json','reports/root/identity-platform.json','reports/discovery/march31-repair-platform.json','reports/discovery/sept29-playbook-platform.json']
catalog_path=Path('product/data/report-catalog.json')
existing=json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
existing_reports={r['id']:r for r in existing.get('reports', [])}
reports=[json.loads(Path(p).read_text()) for p in files]
# This legacy batch refreshes four reports. Preserve newer reviewed episodes
# and their edited display titles instead of silently shrinking the catalog.
for r in reports:
 if r['id'] in existing_reports:r['title']=existing_reports[r['id']]['title']
refreshed={r['id'] for r in reports}
reports.extend(r for r in existing.get('reports', []) if r['id'] not in refreshed)
for r in reports:
 if r['id']=='pages-repair':r['assessments']=[a for a in r['assessments'] if a['dimension_id'] in ['C1','C3']]
 if r['id']=='document-recovery':r['assessments']=[a for a in r['assessments'] if a['dimension_id'] in ['C3','C6']]
catalog=dict(version='behavioral-reports/v1',prepared_at='2026-10-04',method_note=f'Exploratory screening across April 2025–September 2026, followed by {len(reports)} selected episode reconstructions. All 13 structured source tables are indexed; search covers bounded excerpts. These reports do not estimate incident prevalence or rank models.',rubric=json.loads(Path('research/behavioral-rubric.json').read_text())['dimensions'],reports=reports)
Path('product/data/report-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print(f'Assembled {len(reports)} reports, {sum(len(r["timeline"]) for r in reports)} anchors, {len(catalog["rubric"])} rubric dimensions')
