import copy
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from mbse_diagrams.core import DiagramError, validate, svg, viewer, drawio, import_drawio, mermaid

ROOT=Path(__file__).resolve().parents[1]

class InterchangeTests(unittest.TestCase):
    def setUp(self):
        self.d=json.loads((ROOT/'examples/communication/diagram.json').read_text())

    def test_roundtrip_preserves_supported_document(self):
        restored,report=import_drawio(drawio(self.d))
        self.assertEqual(restored,self.d)
        self.assertEqual(report['normalized'],[])

    def test_document_metadata_survives_model_attribute_removal(self):
        root=ET.fromstring(drawio(self.d))
        root.find('diagram/mxGraphModel').attrib.pop('mbseDocument')
        restored,_=import_drawio(ET.tostring(root,encoding='unicode'))
        self.assertEqual(restored,self.d)

    def test_edit_presentation_without_changing_model(self):
        root=ET.fromstring(drawio(self.d))
        node=root.find(".//object[@id='Sender']")
        node.set('label','«part def»\nEdited display')
        node.find('mxCell/mxGeometry').set('x','80')
        restored,report=import_drawio(ET.tostring(root,encoding='unicode'))
        sender=next(n for n in restored['nodes'] if n['id']=='Sender')
        self.assertEqual(sender['label'],'Edited display')
        self.assertEqual(sender['modelRef'],self.d['nodes'][1]['modelRef'])
        self.assertEqual(restored['edges'][0]['points'][0],[200,230])
        self.assertTrue(report['normalized'])

    def test_compartment_text_is_editable(self):
        root=ET.fromstring(drawio(self.d))
        root.find(".//mxCell[@id='Exchange--compartment-0']").set('value','parts\nsender : Sender\nchannel : Channel\nreceiver : Receiver [1]')
        restored,_=import_drawio(ET.tostring(root,encoding='unicode'))
        self.assertEqual(restored['nodes'][-1]['compartments'][0]['lines'][-1],'receiver : Receiver [1]')

    def test_unsupported_model_changes_fail(self):
        root=ET.fromstring(drawio(self.d))
        root.find(".//object[@id='sender-specialization']/mxCell").set('target','Channel')
        with self.assertRaisesRegex(DiagramError,'semantic endpoints'):
            import_drawio(ET.tostring(root,encoding='unicode'))

    def test_unknown_fields_and_dangling_edges_fail(self):
        for mutate in [lambda d:d['nodes'][0].update(parent='unknown'),lambda d:d['edges'][0].update(target='missing')]:
            d=copy.deepcopy(self.d);mutate(d)
            with self.assertRaises(DiagramError):validate(d)

    def test_labels_are_inert_in_svg_and_html(self):
        self.d['nodes'][0]['label']='</script><img src=x onerror=alert(1)>'
        text=viewer(self.d)
        self.assertNotIn('<img src=x',text)
        root=ET.fromstring(svg(self.d))
        self.assertEqual(len(root.findall('.//{http://www.w3.org/2000/svg}script')),0)

    def test_accessibility_and_relationship_markers(self):
        root=ET.fromstring(svg(self.d)); ns={'s':'http://www.w3.org/2000/svg'}
        ids=[x.get('id') for x in root.iter() if x.get('id')]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(root.get('role'),'img')
        self.assertEqual(len(root.findall('.//s:polyline',ns)),2)
        self.assertTrue(all('triangle' in e.get('marker-end','') for e in root.findall('.//s:polyline',ns)))

    def test_mermaid_loss_report_is_explicit(self):
        source,report=mermaid(self.d)
        self.assertIn('flowchart LR',source)
        self.assertIn('model references',report['lost'])
        self.assertIn('notation glyphs',report['lost'])

    def test_uml_profile_and_dependency(self):
        d=json.loads((ROOT/'examples/uml/diagram.json').read_text())
        restored,_=import_drawio(drawio(d));self.assertEqual(restored,d)
        self.assertIn('stroke-dasharray',svg(d))

    def test_compressed_drawio_export(self):
        import base64,zlib
        from urllib.parse import quote
        root=ET.fromstring(drawio(self.d));model=root.find('diagram/mxGraphModel')
        encoder=zlib.compressobj(wbits=-15)
        raw=quote(ET.tostring(model,encoding='unicode')).encode()
        compressed=encoder.compress(raw)+encoder.flush()
        text='<mxfile><diagram>'+base64.b64encode(compressed).decode()+'</diagram></mxfile>'
        restored,_=import_drawio(text);self.assertEqual(restored,self.d)


class SysMLSubsetTests(unittest.TestCase):
    def test_source_mapping_and_relationships(self):
        from mbse_diagrams.sysml import extract
        source=(ROOT/'examples/communication/communication.sysml').read_text()
        d,receipt=extract(source,'communication.sysml')
        self.assertEqual(len(d['nodes']),5)
        self.assertEqual([(e['source'],e['target']) for e in d['edges']],[('Sender','Participant'),('Receiver','Participant')])
        self.assertTrue(d['sources'][0]['revision'].startswith('sha256:'))
        self.assertIn('not run',receipt['languageValidation'])

    def test_unsupported_constructs_are_not_silently_dropped(self):
        from mbse_diagrams.sysml import extract
        for source in ['package P { action def A; }','package P { part def A { attribute x : Real; } }','package P { part def A :> Missing; }']:
            with self.assertRaises(DiagramError):extract(source,'input.sysml')

    def test_mixed_part_item_compartments(self):
        from mbse_diagrams.sysml import extract
        d,_=extract('package P { item def M; part def A { part a : A; item m : M; } }','input.sysml')
        self.assertEqual([c['name'] for c in d['nodes'][1]['compartments']],['parts','items'])

if __name__=='__main__':unittest.main()
