import unittest
from vispipe import Pipeline, block
import logging
logging.disable(logging.CRITICAL)


class TestPipelineOutputs(unittest.TestCase):
    def setUp(self):
        self.pipeline = Pipeline()
        self.node = self.pipeline.add_node('np_iter_file', path='tests/data/10elementarray.npy')

    def tearDown(self):
        self.pipeline.clear_pipeline()

    def test_missing_output(self):
        self.pipeline.run()
        with self.assertRaises(KeyError):
            _ = self.pipeline.outputs[self.node]

    def test_working_output(self):
        self.pipeline.add_output(self.node)
        self.pipeline.run()
        out = list(self.pipeline.outputs[self.node])
        self.assertEqual(list(range(10)), out)

    def test_output_naming(self):
        self.pipeline.get_node(self.node).name = 'named_file'
        self.pipeline.add_output('named_file')
        self.pipeline.run()
        _ = self.pipeline.outputs['named_file']

    def test_output_accessing(self):
        self.pipeline.get_node(self.node).name = 'named_file'
        self.pipeline.add_output('named_file')
        self.pipeline.run()
        access_name = self.pipeline.outputs['named_file']
        with self.assertRaises(KeyError):
            _ = self.pipeline.outputs[self.node]
        access_hash = self.pipeline.get_output(self.node)  # Correctly access the output by hash
        self.assertEqual(access_name, access_hash)


class TestPipelineNodesAndConnections(unittest.TestCase):
    def setUp(self):
        self.pipeline = Pipeline()

    def tearDown(self):
        self.pipeline.clear_pipeline()

    def test_add_node(self):
        node_hash = self.pipeline.add_node(list(self.pipeline._blocks.keys())[0])
        self.assertEqual(len(self.pipeline.nodes), 1)
        self.assertEqual(hash(self.pipeline.nodes[0]), node_hash)

    def test_remove_node(self):
        node_hash = self.pipeline.add_node(list(self.pipeline._blocks.keys())[0])
        self.pipeline.remove_node(node_hash)
        with self.assertRaises(KeyError):
            self.pipeline.get_node(node_hash)

    def test_clear_pipeline(self):
        self.inp = self.pipeline.add_node('np_iter_file', path='tests/data/10elementarray.npy')
        self.k = self.pipeline.add_node('constant', value=2)
        self.collect = self.pipeline.add_node('identity_two')
        self.multiply = self.pipeline.add_node('multiply')
        self.sum = self.pipeline.add_node('accumulate')
        self.pipeline.add_conn(self.inp, 0, self.collect, 0)
        self.pipeline.add_conn(self.k, 0, self.collect, 1)
        self.pipeline.add_conn(self.collect, 0, self.multiply, 0)
        self.pipeline.add_conn(self.collect, 1, self.multiply, 1)
        self.pipeline.add_conn(self.multiply, 0, self.sum, 0)
        self.pipeline.add_output(self.sum)
        self.pipeline.add_macro(self.collect, self.multiply)
        self.pipeline.clear_pipeline()
        self.assertFalse(self.pipeline.nodes)
        self.assertFalse(self.pipeline.macro)
        self.assertFalse(self.pipeline._outputs)
        self.assertFalse(self.pipeline.runner.threads)
        self.assertFalse(self.pipeline.runner.vis_source)


class TestPipelineMacrosAndBlocksAndSaveLoad(unittest.TestCase):
    @block(tag='common', output_names=['y1', 'y2'])
    def identity_two(x, y):
        return x, y

    def setUp(self):
        self.pipeline = Pipeline()
        self.inp = self.pipeline.add_node('np_iter_file', path='tests/data/10elementarray.npy')
        self.k = self.pipeline.add_node('constant', value=2)
        self.collect = self.pipeline.add_node('identity_two')
        self.multiply = self.pipeline.add_node('multiply')
        self.sum = self.pipeline.add_node('accumulate')
        self.pipeline.add_conn(self.inp, 0, self.collect, 0)
        self.pipeline.add_conn(self.k, 0, self.collect, 1)
        self.pipeline.add_conn(self.collect, 0, self.multiply, 0)
        self.pipeline.add_conn(self.collect, 1, self.multiply, 1)
        self.pipeline.add_conn(self.multiply, 0, self.sum, 0)
        self.pipeline.add_output(self.sum)

    def tearDown(self):
        self.pipeline.clear_pipeline()

    def test_intercept_end_accumulate_with_macro(self):
        self.pipeline.add_macro(self.collect, self.multiply)
        self.pipeline.run()
        for value in self.pipeline.outputs[self.sum]:
            self.assertEqual(value, 10 * 9)  # Thanks Gauss

    def test_save_is_equal(self):
        self.pipeline.add_macro(self.collect, self.multiply)
        self.pipeline.run()
        for value in self.pipeline.outputs[self.sum]:
            self.assertEqual(value, 10 * 9)  # Thanks Gauss

        self.pipeline.save('tests/data/test_save.pickle')

        p2 = Pipeline('tests/data/test_save.pickle')
        self.assertEqual(set([hash(n) for n in self.pipeline.nodes]), set([hash(n) for n in p2.nodes]))
        self.assertEqual(set(*self.pipeline.macro), set(*p2.macro))
        self.assertEqual(set(self.pipeline._outputs), set(p2._outputs))
        self.assertEqual(set(self.pipeline.runner.vis_source), set(p2.runner.vis_source))

    def test_end_after_save_load(self):
        self.pipeline.add_macro(self.collect, self.multiply)
        self.pipeline.run()
        for value in self.pipeline.outputs[self.sum]:
            self.assertEqual(value, 10 * 9)  # Thanks Gauss

        self.pipeline.save('tests/data/test_save.pickle')
        self.pipeline.clear_pipeline()
        self.pipeline = Pipeline('tests/data/test_save.pickle')
        self.pipeline.run()
        for value in self.pipeline.outputs[self.sum]:
            self.assertEqual(value, 10 * 9)  # Thanks Gauss

    def test_large(self):
        for i in range(Pipeline.MAXSIZE):
            _ = self.pipeline.add_node('constant')
        self.pipeline.clear_pipeline()

    def test_intercept_end_accumulate(self):
        self.pipeline.run()
        for value in self.pipeline.outputs[self.sum]:
            self.assertEqual(value, 10 * 9)  # Thanks Gauss

    def test_assertions_macro(self):
        # Should assert because self collect is connected to other stuff as well
        with self.assertRaises(Exception):
            self.pipeline.add_macro(self.inp, self.collect)

        self.pipeline.add_output(self.collect)
        with self.assertRaises(Exception):
            self.pipeline.add_macro(self.collect, self.muliply)


if __name__ == '__main__':
    unittest.main()
