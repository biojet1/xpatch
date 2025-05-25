#!/usr/bin/env python
def hey(*s):
	o = None;
	for x in s:
		if o is None:
			from sys import stderr;
			o = stderr.write;
		else:
			o(' ');
		o(str(x));
	o('\n');

NAME = "xpatch.py"
VERSION = "1.1.0"

import re;
srx = re.compile("\s+");

def FileMD5Digest(fname, chunksize = 65536):
	import hashlib;
	m = hashlib.md5();
	f = open(fname, "rb");
	while 1:
		blck = f.read(chunksize);
		if not blck:
			break;
		m.update(blck);
	f.close();
	return m.hexdigest();

def mergeData(a, b):
	A = len(a);
	B = len(b);
	if B > A:
		D = B - A;
		return a + b[A:];
	return a;

def patchDB(patfile, ctx):
	from binascii import unhexlify, hexlify;
	from xml.dom.minidom import parse;
	def dataOf(cur, name):
		cur = cur.getElementsByTagName(name).item(0);
		enc = cur.getAttribute("encoding");
		data = cur.firstChild.data;
		if enc:
			data = dat.encode(enc);
		else:
			data = unhexlify(srx.sub("", data).encode("ascii"));
		return data;
	patches = [];
	meta = {};
	node = parse(patfile).documentElement;
	meta['md5'] = node.getAttribute("md5sum");
	meta['name'] = node.getAttribute("name");
	i = 0;
	for alter in node.getElementsByTagName("alter"):
		i += 1;
		id = alter.getAttribute("id") or ("#%d" % i);
		start = int(alter.getAttribute("start"), 0);
		assert(start >= 0);
		(data_from, data_to) = (dataOf(alter, "from"), dataOf(alter, "to"));
		assert(len(data_from) > 0);
		assert(len(data_to) > 0);
		assert(len(data_to) <= len(data_from));
		length = alter.getAttribute("length");
		if length:
			length = int(length, 0);
		else:
			length = alter.getAttribute("end");
			if length:
				length = (int(length, 0) - start) + 1;
			else:
				length = len(data_from);
		assert(length > 0);
		assert(len(data_from) <= length);
		patches.append({"id": id, "start": start, "length": length, "dataFrom" : data_from, "dataTo" : data_to, "use" : 0});
	if ctx.unPatch:
		hey("Operation: Unpatch");
		for alter in patches:
			dataFrom = alter['dataFrom'];
			dataTo = alter['dataTo'];
			alter['dataFrom'] = mergeData(dataTo, dataFrom);
			alter['dataTo'] = dataFrom;
			assert(len(alter['dataFrom']) == len(alter['dataTo']));
	else:
		hey("Operation: Patch");
	if ctx.bVerbose:
		for alter in patches:
			start = alter['start'];
			length = alter['length'];
			end = start + length - 1;
			dataFrom = alter['dataFrom'];
			dataTo = alter['dataTo'];
			lenFrom = len(dataFrom);
			lenTo = len(dataTo);
			hey("-------------");
			hey("Patch:", alter['id']);
			hey("Range: 0x%X - 0x%X (%d - %d)" % (start, end, start, end));
			hey("Size : %d (0x%X) bytes" % (length, length));
			hey("From :", hexlify(dataFrom[:31]).decode() + "%s (%d)" % (lenFrom > 31 and "..." or "",  lenFrom));
			hey("To   :", hexlify(dataTo[:31]).decode() + "%s (%d)" % (lenTo > 31 and "..." or "",  lenTo));
			#hey("-------------");
	return meta, patches;

def patch(patches, target, ctx):
	from binascii import unhexlify, hexlify;
	use = 0;
	f = open(target, 'rb');
	for alter in patches:
		id = alter['id'];
		length = alter['length'];
		dataFrom = alter['dataFrom'];
		dataTo = alter['dataTo'];
		f.seek(alter['start'], 0);
		data = f.read(length);
		#if ctx.bVerbose:
		#	hey("data :", length, len(data), hexlify(data));
		#	hey("data :", len(dataFrom), hexlify(data[0 : len(dataFrom)]));
		#	hey("data :", len(dataTo), hexlify(data[0 : len(dataTo)]));
		alter['use'] = 0;
		if len(data) != length:
			raise RuntimeWarning("Invalid length %d read for `%s', %d expected " % (len(data), id, length));
		elif dataFrom == data[0 : len(dataFrom)]:
			alter['use'] = 1;
			use += 1;
		elif dataTo == data[0 : len(dataTo)]:
			hey("Skipping:",id);
		else :
			hey("Invalid:",id);
	f.close();
	if use > 0:
		f = ctx.dryRun and open(target, 'rb') or open(target, 'r+b');
		for alter in patches:
			if alter['use']:
				id = alter['id'];
				start = alter['start'];
				dataTo = alter['dataTo'];
				hey("Applying:",id);
				f.seek(start);
				ctx.dryRun or f.write(dataTo);
		f.close();

def main():
# + Helper fundtions
	def check_md5(file, md5):
		fmd5 = FileMD5Digest(file);
		if fmd5 == md5:
			hey("MD5: OK %s" % (md5));
		else:
			hey("Error: Invalid MD5 %s != %s" % (fmd5, md5));
# + Options
	from optparse import OptionParser;
	ctx = OptionParser(version = "1.0");
#	ctx.add_option("-f", action = "store", dest = "file", help="The file to patch.");
	ctx.add_option("-n", "--dry-run", action = "store_true", dest = "dryRun", help="Test only dont patch.");
	ctx.add_option("-u", action = "store_true", dest = "unPatch", help="unpatch.");
	ctx.add_option("-v", action = "store_true", dest = "bVerbose", help="verbose.");
	ctx.add_option("-m", action = "store_true", dest = "bVerify", help="check md5 digest if given.");
	(ctx, args) = ctx.parse_args();
	if len(args) > 0:
		args.reverse();
		patfile = args.pop();
		hey("Patch:", patfile);
		(meta, patches) = patchDB(patfile, ctx);
		while len(args) > 0:
			target = args.pop();
			hey("Source:", target);
			(not ctx.dryRun) and (not ctx.unPatch) and ctx.bVerify and meta['md5'] and check_md5(target, meta['md5']);
			patch(patches, target, ctx);
			(not ctx.dryRun) and ctx.unPatch and ctx.bVerify and meta['md5'] and check_md5(target, meta['md5']);

if __name__ == "__main__":
	import sys;
	sys.exit(main());
