from vispipe import vispipe
import numpy as np
import math
import time


@vispipe.block
def three_args(arg1=5, arg2='ciao', arglonglong='7x7'):
    yield arg1


@vispipe.block
def some_list():
    yield [0, 1, 2, 3, 4, 5, 42]


@vispipe.block
def five_args(arg1=5, arg2='ciao', arglong='7x7', longveryarg=1023, onemore=-100.3):
    yield 1


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
def image_rgb(r, g, b):
    time.sleep(1)
    ones = np.ones((28, 28, 1))
    yield np.concatenate([r * ones, g * ones, b * ones, ones * 255], axis=-1)


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
    print('Value: %s' % input1)
    yield None


@vispipe.block(tag='vis', data_type='image')
def test_vis(input1):
    yield input1


@vispipe.block(tag='vis', data_type='raw')
def test_vis_raw(input1):
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


@vispipe.block
class testfull:
    def __init__(self):
        self.iterator = None

    def run(self, input1):
        if self.iterator is None:
            self.iterator = iter(input1)

        try:
            x = vispipe.pipeline._skip(next(self.iterator))
        except StopIteration:
            self.iterator = None
            x = StopIteration
        yield x


@vispipe.block
class timer:
    def __init__(self):  #TODO: once implemented init params set n here
        self.n = 1000
        self.start_n = self.n
        self.started = False
        self.last_result = 'Still counting'

    def run(self, x):
        if not self.started:
            self.started = True
            self.start_time = time.time()
        self.n -= 1
        if self.n == -1:
            end_time = time.time()
            delta = end_time - self.start_time
            self.last_result = 'Benchmark - %s runs | time: %s | r/s: %s' % (self.start_n, delta, round(self.start_n / delta, 4))
            self.n = self.start_n
            self.start_time = time.time()
        yield self.last_result


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
twoout = vispipe.pipeline._blocks['test_identity_2_out']
lister = vispipe.pipeline._blocks['some_list']
timerb = vispipe.pipeline._blocks['timer']

from vispipe.ops import flows
iterator = vispipe.pipeline._blocks['iterator']
#iterator = vispipe.pipeline._blocks['testfull']
iterator_add = vispipe.pipeline.add_node(iterator)
listid = vispipe.pipeline.add_node(lister)
timerbid = vispipe.pipeline.add_node(timerb)
out_test_id = vispipe.pipeline.add_node(out_test)

vispipe.pipeline.add_conn(lister, listid, 0, iterator, iterator_add, 0)
vispipe.pipeline.add_conn(iterator, iterator_add, 0, timerb, timerbid, 0)
vispipe.pipeline.add_conn(timerb, timerbid, 0, out_test, out_test_id, 0)

vispipe.pipeline.build()
vispipe.pipeline.run()
#
#vispipe.pipeline.unbuild()
#vispipe.pipeline.build()
#vispipe.pipeline.run()

print(42)
while True:
    continue
