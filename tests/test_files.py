from pathlib import Path
import os
import unittest
from unittest.mock import patch
from storytold_tools.common import absolute,child,create_new,encoded,parse_json,snapshot,StorytoldError
from tests.support import WorkspaceCase

class FileSafetyTests(WorkspaceCase):
    def test_json_rejects_duplicates(self):
        with self.assertRaises(StorytoldError): parse_json(b'{"a":1,"a":2}')
    def test_json_rejects_nonfinite_numbers(self):
        for token in (b'NaN',b'Infinity',b'-Infinity'):
            with self.subTest(token=token),self.assertRaises(StorytoldError): parse_json(token)
    def test_json_rejects_invalid_utf8(self):
        with self.assertRaises(StorytoldError): parse_json(b'"\xff"')
    def test_json_byte_limit(self):
        with self.assertRaises(StorytoldError): parse_json(b'{}',limit=1)
    def test_json_preserves_types(self):
        value={'number':3,'truth':True,'nothing':None,'error':{'code':'DIV0'}}
        self.assertEqual(parse_json(encoded(value)),value)
    def test_rejects_relative_absolute_paths(self):
        with self.assertRaises(StorytoldError): absolute('relative')
    def test_rejects_traversal(self):
        with self.assertRaises(StorytoldError): absolute(self.base/'..'/'escape')
    def test_rejects_unc(self):
        for p in ('//server/share','\\\\server\\share'):
            with self.subTest(path=p),self.assertRaises(StorytoldError): absolute(p)
    def test_child_rejects_escaping_names(self):
        for name in ('../escape','/absolute','a//b','a/./b','x\\y','C:thing'):
            with self.subTest(name=name),self.assertRaises(StorytoldError): child(self.work,name)
    def test_create_new_is_noclobber(self):
        p=self.work/'outputs/a';create_new(p,b'original')
        with self.assertRaises((OSError,StorytoldError)): create_new(p,b'replacement')
        self.assertEqual(p.read_bytes(),b'original')
    def test_atomic_publication_failure_does_not_leave_output(self):
        p=self.work/'outputs/new'
        with patch('storytold_tools.common.os.link',side_effect=OSError('unsupported filesystem')):
            with self.assertRaises(OSError): create_new(p,b'data')
        self.assertFalse(p.exists())
        self.assertEqual(list(p.parent.glob('.storytold-write-*')),[])
    def test_missing_parent_is_not_created(self):
        with self.assertRaises(StorytoldError): create_new(self.work/'absent/data',b'data')
        self.assertFalse((self.work/'absent').exists())
    def test_symlink_output_and_ancestor_rejected(self):
        outside=self.base/'outside';outside.mkdir();(outside/'keep').write_bytes(b'keep')
        link=self.work/'outputs/link'
        try: link.symlink_to(outside,target_is_directory=True)
        except OSError as e: self.skipTest('OS symlink creation unavailable: '+str(e))
        with self.assertRaises(StorytoldError): create_new(link/'keep',b'replace')
        self.assertEqual((outside/'keep').read_bytes(),b'keep')
    def test_snapshot_byte_limit(self):
        p=self.base/'big';p.write_bytes(b'12345')
        with self.assertRaises(StorytoldError): snapshot(p,limit=4)
    def test_snapshot_rejects_directory(self):
        with self.assertRaises(StorytoldError): snapshot(self.base)
    def test_new_file_has_one_link(self):
        p=self.work/'outputs/file';create_new(p,b'data')
        self.assertEqual(p.stat().st_nlink,1)

    def test_snapshot_opens_in_binary_mode(self):
        # Simulated on this OS: Windows os.open defaults to text mode, which would alter hashed bytes.
        import storytold_tools.common as common
        p=self.base/'crlf.bin';p.write_bytes(b'a\r\n\x1ab');seen=[];real_open=os.open
        def record(path,flags,*args):
            seen.append(flags)
            return real_open(path,flags if os.name=='nt' else flags&~0x8000,*args)
        with patch.object(common.os,'O_BINARY',0x8000,create=True),patch.object(common.os,'open',side_effect=record):
            self.assertEqual(snapshot(p,body=True)[2],b'a\r\n\x1ab')
        self.assertTrue(seen and seen[0]&0x8000)

    def test_json_exponent_overflow_rejected(self):
        with self.assertRaises(StorytoldError):
            parse_json(b'{"count":1e9999}')

    def test_windows_readonly_publication_order_simulated(self):
        # Exercise the ordering branch on this OS; not a native Windows result.
        import stat
        original_link=os.link
        def link(source,target,**kwargs):
            self.assertTrue(Path(source).stat().st_mode & stat.S_IWUSR)
            return original_link(source,target,**kwargs)
        p=self.work/'outputs/readonly'
        with patch('storytold_tools.common.IS_WINDOWS',True):
            with patch('storytold_tools.common.os.link',side_effect=link):
                create_new(p,b'data',mode=0o400)
        self.assertEqual(p.stat().st_nlink,1)
        self.assertEqual(list(p.parent.glob('.storytold-write-*')),[])
