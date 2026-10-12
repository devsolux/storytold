import io
import json
import os
from pathlib import Path
import unittest
import wave
import zipfile
from storytold_tools.common import create_new,encoded,StorytoldError
from storytold_tools.workspace import init_workspace,stage,verify_inputs,verify_artifact,inspect_bytes
from tests.support import WorkspaceCase

class WorkspaceTests(WorkspaceCase):
    def original(self,body=b'original bytes'):
        p=self.base/'source.txt';p.write_bytes(body);return p
    def test_refuses_existing_workspace(self):
        with self.assertRaises(StorytoldError): init_workspace(self.work)
    def test_stage_preserves_original_and_writes_receipt(self):
        p=self.original();r=stage(self.work,p)
        self.assertEqual(p.read_bytes(),b'original bytes')
        self.assertEqual((self.work/r['staged_path']).read_bytes(),p.read_bytes())
        self.assertTrue(Path(r['receipt']).is_file());self.assertTrue(verify_inputs(self.work)['all_unchanged'])
    def test_stage_collision_refuses_overwrite(self):
        p=self.original();stage(self.work,p)
        with self.assertRaises(StorytoldError): stage(self.work,p)
    def test_stage_requires_external_original(self):
        p=self.work/'outputs/new';p.write_bytes(b'new')
        with self.assertRaises(StorytoldError): stage(self.work,p)
    def test_stage_rejects_empty_input(self):
        with self.assertRaises(StorytoldError): stage(self.work,self.original(b''))
    def test_stage_rejects_escape_name(self):
        with self.assertRaises(StorytoldError): stage(self.work,self.original(),'../escape')
    def test_original_changed_is_not_success(self):
        p=self.original();stage(self.work,p);p.write_bytes(b'changed')
        with self.assertRaises(StorytoldError): verify_inputs(self.work)
    def test_staged_changed_is_not_success(self):
        p=self.original();r=stage(self.work,p);s=self.work/r['staged_path'];s.chmod(0o600);s.write_bytes(b'changed')
        with self.assertRaises(StorytoldError): verify_inputs(self.work)
    def test_no_receipts_is_not_success(self):
        with self.assertRaises(StorytoldError): verify_inputs(self.work)
    def test_cross_workspace_receipt_rejected(self):
        p=self.original();r=stage(self.work,p);receipt=Path(r['receipt']);v=json.loads(receipt.read_text());v['workspace_id']='unrelated';receipt.write_bytes(encoded(v))
        with self.assertRaises(StorytoldError): verify_inputs(self.work)
    def test_verification_rejects_inputs_as_outputs(self):
        stage(self.work,self.original())
        with self.assertRaises(StorytoldError): verify_artifact(self.work,'inputs/source.txt','txt')
    def test_verification_rejects_empty_file(self):
        p=self.work/'outputs/empty';p.write_bytes(b'')
        with self.assertRaises(StorytoldError): verify_artifact(self.work,'outputs/empty','bytes')
    def test_verification_rejects_hardlinked_output(self):
        p=self.original();os.link(p,self.work/'outputs/hardlink')
        with self.assertRaises(StorytoldError): verify_artifact(self.work,'outputs/hardlink','txt')
    def test_json_artifact_keeps_verification_scope_honest(self):
        (self.work/'outputs/data.json').write_bytes(encoded({'x':3}))
        r=verify_artifact(self.work,'outputs/data.json','json')
        self.assertEqual(r['check_level'],'parsed');self.assertFalse(r['native_reopen_verified'])
        self.assertFalse(r['visual_review_verified']);self.assertFalse(r['format_fidelity_verified'])
    def test_digest_mismatch_is_failure(self):
        (self.work/'outputs/file').write_bytes(b'data')
        with self.assertRaises(StorytoldError): verify_artifact(self.work,'outputs/file','bytes','0'*64)
    def test_pdf_check_is_only_signature(self):
        level,_=inspect_bytes(b'%PDF-1.7\nsynthetic not a valid PDF\n%%EOF','pdf')
        self.assertEqual(level,'signature_only')
    def test_svg_entities_rejected(self):
        with self.assertRaises(StorytoldError): inspect_bytes(b'<!DOCTYPE svg [<!ENTITY test "bad">]><svg/>','svg')
    def test_wav_pcm_parse_and_duration(self):
        out=io.BytesIO()
        with wave.open(out,'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\0\0'*800)
        level,facts=inspect_bytes(out.getvalue(),'wav')
        self.assertEqual(level,'parsed_pcm');self.assertEqual(facts['duration_seconds'],0.1)
    def test_wav_truncation_rejected(self):
        out=io.BytesIO()
        with wave.open(out,'wb') as f:
            f.setnchannels(1);f.setsampwidth(2);f.setframerate(8000);f.writeframes(b'\0\0'*800)
        with self.assertRaises(StorytoldError): inspect_bytes(out.getvalue()[:-20],'wav')
    def test_ooxml_structural_not_fidelity(self):
        for fmt,main in [('docx','word/document.xml'),('xlsx','xl/workbook.xml'),('pptx','ppt/presentation.xml')]:
            with self.subTest(fmt=fmt):
                out=io.BytesIO()
                with zipfile.ZipFile(out,'w') as z:
                    z.writestr('[Content_Types].xml','<Types/>');z.writestr(main,'<synthetic/>')
                level,facts=inspect_bytes(out.getvalue(),fmt);self.assertEqual(level,'structural_only')
    def test_ooxml_missing_main_rejected(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z: z.writestr('[Content_Types].xml','<Types/>')
        with self.assertRaises(StorytoldError): inspect_bytes(out.getvalue(),'docx')
    def test_ooxml_path_escape_rejected(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('word/document.xml','<doc/>');z.writestr('../escape','bad')
        with self.assertRaises(StorytoldError): inspect_bytes(out.getvalue(),'docx')

    def test_container_decompression_error_is_validation_failure(self):
        import zlib
        from unittest.mock import patch
        (self.work/'outputs/data.docx').write_bytes(b'synthetic placeholder')
        with patch('storytold_tools.workspace.inspect_bytes',side_effect=zlib.error('synthetic inflate failure')):
            with self.assertRaises(StorytoldError): verify_artifact(self.work,'outputs/data.docx','docx')

    def test_utf16_dtd_cannot_bypass_xml_guard(self):
        p=self.work/'outputs/unsafe.svg'
        p.write_bytes(('<?xml version="1.0" encoding="UTF-16"?>'
                       '<!DOCTYPE svg [<!ENTITY a "EXPANDED">]><svg>&a;</svg>').encode('utf-16'))
        with self.assertRaises((StorytoldError,UnicodeError)):
            verify_artifact(self.work,'outputs/unsafe.svg','svg')

    def test_deleted_receipt_cannot_hide_existing_staged_input(self):
        source_a=self.base/'a.txt';source_a.write_text('a')
        source_b=self.base/'b.txt';source_b.write_text('b')
        first=stage(self.work,source_a)
        stage(self.work,source_b)
        Path(first['receipt']).unlink()
        with self.assertRaises(StorytoldError):
            verify_inputs(self.work)

    def test_duplicate_receipts_do_not_double_count_input(self):
        source=self.base/'source.txt';source.write_text('a')
        receipt=stage(self.work,source)
        (self.work/'receipts/input-duplicate.json').write_bytes(Path(receipt['receipt']).read_bytes())
        with self.assertRaises(StorytoldError):
            verify_inputs(self.work)

    def test_receipt_failure_preserves_copy_without_claiming_success(self):
        from unittest.mock import patch
        from storytold_tools.common import create_new
        source=self.base/'original.txt';source.write_text('original')
        def publish(path,data,mode=0o600):
            if path.parent.name=='receipts':
                raise OSError('synthetic receipt publication failure')
            return create_new(path,data,mode)
        with patch('storytold_tools.workspace.create_new',side_effect=publish):
            with self.assertRaisesRegex(StorytoldError,'staging is incomplete'):
                stage(self.work,source)
        self.assertEqual(source.read_text(),'original')
        self.assertEqual((self.work/'inputs/original.txt').read_text(),'original')
        with self.assertRaises(StorytoldError):
            verify_inputs(self.work)
