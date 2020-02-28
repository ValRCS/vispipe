from vispipe import vispipe
import numpy as np
import math

import time


@vispipe.block
def no_input():
    yield 1


@vispipe.block
def image():
    time.sleep(1)
    yield np.concatenate([np.random.randint(0, 255, size=(28, 28, 3)), np.ones((28, 28, 1)) * 255], axis=-1)


@vispipe.block
def image_plus(x):
    time.sleep(1)
    yield np.concatenate([x * np.ones((28, 28, 3)), np.ones((28, 28, 1)) * 255], axis=-1)


@vispipe.block
def test_plus100(x):
    yield x + 100


@vispipe.block
def multiply100(x):
    yield x * 100


@vispipe.block
def rand():
    yield np.random.randn()

@vispipe.block
def randint():
    yield np.random.randint(0, 255)


@vispipe.block
def rand_range(min=-1., max=1.):
    yield (np.random.random() * (max - min)) - min


@vispipe.block
def test_identity(input1):
    yield input1


@vispipe.block(output_names=['y1', 'y2'])
def test_identity_2_out(input1):
    yield input1, input1 + 1


@vispipe.block
def test_plus1(input1):
    yield input1 + 1


@vispipe.block
def test_addition(input1, input2):
    yield input1 + input2


@vispipe.block
def sin(input1):
    yield math.sin(input1)


@vispipe.block
def custom_high_gain_test(input1):
    yield input1


@vispipe.block
def another_1(input1):
    yield 0


@vispipe.block
def another_2(input1):
    yield 0


@vispipe.block
def another_3(input1):
    yield 0


@vispipe.block
def another_4(input1):
    yield 0


@vispipe.block
def in_5(input1, input2, input3, input4, input5):
    yield 0


@vispipe.block
def in_2(input1, input2):
    yield 0


@vispipe.block
def in_3(input1, input2, input3):
    yield 0


@vispipe.block
def print_test(input1):
    print('I am a print block and my value is %s' % input1)
    yield None


@vispipe.block(tag='vis', data_type='image')
def test_vis(input1):
    yield input1


@vispipe.block
class classex:
    def __init__(self):
        self.last_element = None

    def run(self, input1):
        print('I am a print block CLASS and last value was %s while now is %s' % (
            self.last_element, input1))
        self.last_element = input1
        yield None


@vispipe.block
class testempty:
    def __init__(self):
        self.count = 0
        self.sum = 0

    def run(self, input1):
        if self.count == 10:
            val = self.sum
            self.sum = 0
            self.count = 0
            yield val
        else:
            self.sum += input1
            self.count += 1
            yield vispipe.pipeline._empty

# Pipeline Test
custom_add = vispipe.pipeline._blocks['test_addition']
custom_sin = vispipe.pipeline._blocks['sin']
custom_noinp = vispipe.pipeline._blocks['no_input']
custom_rand = vispipe.pipeline._blocks['rand_range']
two_out = vispipe.pipeline._blocks['test_identity_2_out']
out_test = vispipe.pipeline._blocks['print_test']
out_test_class = vispipe.pipeline._blocks['classex']
classempty = vispipe.pipeline._blocks['testempty']
testvis = vispipe.pipeline._blocks['test_vis']

randonode = vispipe.pipeline.add_node(custom_rand, min=0, max=np.pi / 2)
#output_print = vispipe.pipeline.add_node(out_test)
sinnode = vispipe.pipeline.add_node(custom_sin)
printnode = vispipe.pipeline.add_node(out_test)
#empty = vispipe.pipeline.add_node(classempty)

# Constant input are attached to sum which returns 2
vispipe.pipeline.add_conn(randonode, 0, sinnode, 0)
#vispipe.pipeline.add_conn(custom_sin, sinidx, 0, classempty, empty, 0)
#vispipe.pipeline.add_conn(classempty, empty, 0, out_test, output_print, 0)
vispipe.pipeline.add_conn(sinnode, 0, printnode, 0)

#print(vispipe.pipeline.pipeline.adj_list)
#vispipe.pipeline.build()
#vispipe.pipeline.run()
#vispipe.pipeline.unbuild()

#vispipe.pipeline.save('./')
#vispipe.pipeline.build()
#vispipe.pipeline.clear_pipeline()

#vispipe.pipeline.load('./')
vispipe.pipeline.build()
vispipe.pipeline.run()

#vispipe.pipeline.unbuild()
#vispipe.pipeline.build()
#vispipe.pipeline.run()

print(42)
while True:
    continue
