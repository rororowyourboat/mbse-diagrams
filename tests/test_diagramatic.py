"""Optional integration tests against the real diagramatic checkout."""
import copy
import json
import os
from pathlib import Path
import unittest
from mbse_diagrams.core import DiagramError
from mbse_diagrams.diagramatic import layout

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(os.environ.get('DIAGRAMATIC_PATH'),'requires explicit trusted DIAGRAMATIC_PATH')
class DiagramaticIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.d=json.loads((ROOT/'examples/communication/diagram.json').read_text())
        self.path=os.environ['DIAGRAMATIC_PATH']
        self.layers={'Participant':'types','Sender':'participants','Receiver':'participants','Channel':'transport','Exchange':'context'}

    def test_real_grid_preserves_engineering_fields(self):
        original=copy.deepcopy(self.d)
        result,receipt=layout(self.d,self.path,layers=self.layers)
        self.assertEqual(self.d,original)
        for before,after in zip(original['nodes'],result['nodes']):
            self.assertEqual({k:v for k,v in before.items() if k!='bounds'},{k:v for k,v in after.items() if k!='bounds'})
            self.assertEqual(before['bounds'][2:],after['bounds'][2:])
        for before,after in zip(original['edges'],result['edges']):
            self.assertEqual({k:v for k,v in before.items() if k!='points'},{k:v for k,v in after.items() if k!='points'})
        self.assertEqual(receipt['checks']['nodeOverlap'],'passed')
        self.assertEqual(receipt['engine']['commit'],'baba9c95ea4b2783ae77d205bd958745d6eb9b83')

    def test_reverse_direction_and_incomplete_layers_keep_every_node(self):
        for direction in ('TB','BT','LR','RL'):
            result,_=layout(self.d,self.path,direction,{'Participant':'types'})
            self.assertEqual({n['id'] for n in result['nodes']},{n['id'] for n in self.d['nodes']})
            self.assertTrue(all(n['bounds'][0]>=0 and n['bounds'][1]>=0 for n in result['nodes']))

    def test_unknown_layer_node_is_rejected(self):
        with self.assertRaisesRegex(DiagramError,'unknown node'):
            layout(self.d,self.path,layers={'missing':'types'})
