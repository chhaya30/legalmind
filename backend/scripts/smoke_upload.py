import os, sys, time, json, urllib.request
from pathlib import Path
BASE=os.getenv('LEGALMIND_URL','http://127.0.0.1:8000/api/v1')
path=Path(sys.argv[1]) if len(sys.argv)>1 else Path('tests/fixtures/sample_judgment.pdf')
boundary='----LegalMindSmokeBoundary'
data=path.read_bytes(); body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\nContent-Type: application/pdf\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
req=urllib.request.Request(BASE+'/documents/upload',data=body,method='POST',headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})
with urllib.request.urlopen(req,timeout=30) as r: accepted=json.loads(r.read()); print('accepted',accepted)
doc_id=accepted['id']
for _ in range(60):
    with urllib.request.urlopen(BASE+f'/documents/{doc_id}',timeout=10) as r: doc=json.loads(r.read())
    print('status',doc['status'])
    if doc['status'] in {'ready','failed'}:
        if doc['status']=='failed': raise SystemExit('processing failed: '+str(doc.get('error_message')))
        print('Smoke upload passed:',doc_id); break
    time.sleep(1)
else: raise SystemExit('processing timeout')
