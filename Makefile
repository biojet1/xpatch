build: .build/xpatch.src

.build/xpatch.src: xpatch.src.py
	scrpp -I. -I.../_inc/python xpatch.src.py | python  -c "import os,sys; a=os.fdopen(0,'Ub').read(); len(a) > 0 and open(sys.argv[1],'wb',16777216).write(a);" $@

### CMDREF
.build/cmdref.xml: doc/cmdref.src.xml
	dbproc --type=cmdref --src $? --out $@
.build/manual.html: doc/*.x*l .build/cmdref.xml
	dbproc --type=html --src doc/manual.xml --out $@
cutdoc: .build/manual.html
	lynx -nolist -dump -width=80 $? | python -c "import sys, json; print '\n'.join([json.dumps(x.rstrip() + '\n')  for x in sys.stdin.readlines() if x.rstrip()])" | perl -ne "if(/\s*(Links|Example)\s*/){exit(0)}else{print}" | gclip
man: .build/manual.html
### CMDREF
