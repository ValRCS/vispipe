from vispipe import Pipeline
from flask_socketio import SocketIO
from threading import Thread, Event
from flask import Flask, render_template, session
from vispipe.server.server_gui import CursesQueueGUI
import numpy as np
import cv2
import traceback
import os
import logging
import time
log = logging.getLogger('vispipe')
log.setLevel(logging.DEBUG)
app = Flask(__name__)
socketio = SocketIO(app, async_mode=None, logger=False, engineio_logger=False)


class Server:
    gui_thread = Thread()
    vis_thread = Thread()
    vis_thread.daemon = True
    vis_thread_stop_event = Event()
    qsize_thread_stop_event = Event()
    SESSION_TYPE = 'redis'

    def __init__(self, slow=True, PATH_CKPT='./scratch_test.pickle', use_curses=True):
        self.pipeline = Pipeline()
        self.PATH_CKPT = PATH_CKPT
        self.slow = slow

        # Run the actual server wrapped inside socketio
        app.config.from_object(__name__)
        app.config['SECRET_KEY'] = 'secret!'
        app.config['DEBUG'] = True
        socketio.on_event('new_node', self.new_node)
        socketio.on_event('remove_node', self.remove_node)
        socketio.on_event('new_conn', self.new_conn)
        socketio.on_event('set_custom_arg', self.set_custom_arg)
        socketio.on_event('run_pipeline', self.run_pipeline)
        socketio.on_event('stop_pipeline', self.stop_pipeline)
        socketio.on_event('clear_pipeline', self.clear_pipeline)
        socketio.on_event('save_nodes', self.save_nodes)
        socketio.on_event('connect', self.connect)
        socketio.on_event('disconnect', self.disconnect)

        self.gui = None
        if use_curses:
            self.gui = CursesQueueGUI()
            if not self.gui_thread.isAlive():
                logging.info('Launching terminal queue visualization')
                self.gui_thread = Thread(target=self.set_qsize)
                self.gui_thread.daemon = True
                self.gui_thread.start()
            time.sleep(0.2)

        socketio.run(app)

    @app.route('/')
    def index():
        session['test_session'] = 42
        return render_template('index.html')

    @app.route('/get/')
    def show_session():
        log.info(session['test_session'])
        return '%s' % session.get('test_session')

    def share_blocks(self):
        for block in self.pipeline.get_blocks(serializable=True):
            socketio.emit('new_block', block)
        socketio.emit('end_block', None)

    def new_node(self, block):
        try:
            log.info('New node')
            node_hash = hash(self.pipeline.add_node(block['name']))
            return {'id': node_hash}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500

    def remove_node(self, node_hash):
        try:
            log.info('Removing node')
            self.pipeline.remove_node(node_hash)
            return {}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500

    def new_conn(self, x):
        try:
            self.pipeline.add_conn(x['from_hash'], x['out_idx'], x['to_hash'], x['inp_idx'])
            return {}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500

    def set_custom_arg(self, data):
        try:
            self.pipeline.set_custom_arg(data['id'], data['key'], data['value'])
            return {}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500

    def process_image(self, x):
        x = np.array(x, dtype=np.uint8)  # Cast to int
        if x.ndim in [0, 1, 4]:
            raise Exception('The format image you passed is not visualizable')

        if x.ndim == 2:  # Convert from gray to rgb
            x = cv2.cvtColor(x, cv2.COLOR_GRAY2RGB)
        if x.shape[-1] == 3:  # Add alpha channel
            x = np.concatenate([x, 255 * np.ones((x.shape[0], x.shape[1], 1))], axis=-1)
        shape = x.shape
        return np.reshape(x, (-1,)).tolist(), shape

    def send_vis(self, vis_thread_stop_event):
        while not vis_thread_stop_event.isSet():
            try:
                vis = self.pipeline.runner.read_vis()
                for node_hash, value in vis.items():
                    node = self.pipeline.get_node(int(node_hash))
                    if node.block.data_type == 'image':
                        value, shape = self.process_image(value)
                    elif node.block.data_type == 'raw':
                        if isinstance(value, (np.ndarray, list)):
                            try:
                                value = np.around(value, 2)
                            except Exception:
                                log.error('The value is a numpy array or list that is not roundable')
                        elif isinstance(value, float):
                            value = round(value, 2)
                        value = str(value)

                    socketio.emit('send_vis', {**{'id': node_hash, 'value': value}, **node.block.serialize()})
            except Exception as e:
                log.error(traceback.format_exc())
                socketio.emit('message', str(e))
            socketio.sleep(0.5)

    def set_qsize(self):
        while True:
            try:
                values = self.pipeline.read_qsize()
                for h, name, q, qmax in values:
                    self.gui.set_queues(h, name, q, qmax)
                self.gui.clear_queues()
            except Exception:
                log.error(traceback.format_exc())
            time.sleep(1)

    def run_pipeline(self):
        try:
            if not self.pipeline.runner.built:
                self.pipeline.build()

            self.pipeline.run(slow=self.slow)
            self.vis_thread_stop_event.clear()
            if not self.vis_thread.isAlive():
                self.vis_thread = socketio.start_background_task(self.send_vis,
                                                                 self.vis_thread_stop_event)
            return {}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500
        return 'Invalid State Encountered', 500

    def stop_pipeline(self):
        try:
            self.vis_thread_stop_event.set()
            self.pipeline.unbuild()
            if self.vis_thread.isAlive():
                self.vis_thread.join()
            return {}, 200
        except Exception as e:
            return str(e), 500

    def clear_pipeline(self):
        try:
            self.stop_pipeline()
            self.pipeline.clear_pipeline()
            return {}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500

    def save_nodes(self, vis_data):
        try:
            self.pipeline.save(self.PATH_CKPT, vis_data)
            log.info('Saved checkpoint')
            return {}, 200
        except Exception as e:
            log.error(traceback.format_exc())
            return str(e), 500

    def load_checkpoint(self, path):
        if not os.path.isfile(path):
            return

        _, vis_data = self.pipeline.load(path)
        pipeline_def = {'nodes': [], 'blocks': [], 'connections': [], 'custom_args': []}
        for node in self.pipeline.nodes():
            pipeline_def['nodes'].append(hash(node))
            conn = self.pipeline.connections(hash(node), out=True)
            pipeline_def['connections'].append([(hash(n), i, j) for n, i, j, _ in conn])
            pipeline_def['blocks'].append(node.block.serialize())
            pipeline_def['custom_args'].append(node.block.serialize_args(node.custom_args))
        socketio.emit('load_checkpoint', {'vis_data': vis_data, 'pipeline': pipeline_def})

    def connect(self):
        log.warning('Client connected')
        self.pipeline.clear_pipeline()

        log.info('Sharing blocks')
        self.share_blocks()

        log.info('Loading checkpoint from %s' % self.PATH_CKPT)
        self.load_checkpoint(self.PATH_CKPT)

        socketio.emit('set_auto_save', True)

    def disconnect(self):
        log.warning('Client disconnected')


if __name__ == '__main__':
    Server()
