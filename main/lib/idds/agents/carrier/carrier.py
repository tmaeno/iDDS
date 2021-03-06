#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0OA
#
# Authors:
# - Wen Guan, <wen.guan@cern.ch>, 2019 - 2020

import datetime
import traceback
try:
    # python 3
    from queue import Queue
except ImportError:
    # Python 2
    from Queue import Queue

from idds.common.constants import (Sections, ProcessingStatus, ProcessingLocking)
from idds.common.utils import setup_logging
from idds.core import (transforms as core_transforms,
                       processings as core_processings)
from idds.agents.common.baseagent import BaseAgent

setup_logging(__name__)


class Carrier(BaseAgent):
    """
    Carrier works to submit and running tasks to WFMS.
    """

    def __init__(self, num_threads=1, poll_time_period=10, retrieve_bulk_size=None,
                 message_bulk_size=1000, **kwargs):
        super(Carrier, self).__init__(num_threads=num_threads, **kwargs)
        self.config_section = Sections.Carrier
        self.poll_time_period = int(poll_time_period)
        self.retrieve_bulk_size = int(retrieve_bulk_size)
        self.message_bulk_size = int(message_bulk_size)

        self.new_task_queue = Queue()
        self.new_output_queue = Queue()
        self.running_task_queue = Queue()
        self.running_output_queue = Queue()

    def init(self):
        status = [ProcessingStatus.New, ProcessingStatus.Submitting, ProcessingStatus.Submitted,
                  ProcessingStatus.Running, ProcessingStatus.FinishedOnExec]
        core_processings.clean_next_poll_at(status)

    def get_new_processings(self):
        """
        Get new processing
        """
        processing_status = [ProcessingStatus.New]
        processings = core_processings.get_processings_by_status(status=processing_status, locking=True, bulk_size=self.retrieve_bulk_size)

        self.logger.debug("Main thread get %s [new] processings to process" % len(processings))
        if processings:
            self.logger.info("Main thread get %s [new] processings to process" % len(processings))
        return processings

    def process_new_processing(self, processing):
        work = processing['processing_metadata']['work']
        work.submit_processing()
        return {'processing_id': processing['processing_id'],
                'status': ProcessingStatus.Submitted,
                'next_poll_at': datetime.datetime.utcnow() + datetime.timedelta(seconds=self.poll_time_period),
                'processing_metadata': processing['processing_metadata']}

    def process_new_processings(self):
        ret = []
        while not self.new_task_queue.empty():
            try:
                processing = self.new_task_queue.get()
                if processing:
                    self.logger.info("Main thread processing new processing: %s" % processing)
                    ret_processing = self.process_new_processing(processing)
                    if ret_processing:
                        ret.append(ret_processing)
            except Exception as ex:
                self.logger.error(ex)
                self.logger.error(traceback.format_exc())
        return ret

    def finish_new_processings(self):
        while not self.new_output_queue.empty():
            processing = self.new_output_queue.get()
            self.logger.info("Main thread submitted new processing: %s" % (processing['processing_id']))
            processing_id = processing['processing_id']
            if 'next_poll_at' not in processing:
                processing['next_poll_at'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.poll_time_period)
            del processing['processing_id']
            processing['locking'] = ProcessingLocking.Idle
            # self.logger.debug("wen: %s" % str(processing))
            core_processings.update_processing(processing_id=processing_id, parameters=processing)

    def get_running_processings(self):
        """
        Get running processing
        """
        processing_status = [ProcessingStatus.Submitting, ProcessingStatus.Submitted, ProcessingStatus.Running, ProcessingStatus.FinishedOnExec]
        processings = core_processings.get_processings_by_status(status=processing_status,
                                                                 # time_period=self.poll_time_period,
                                                                 locking=True,
                                                                 bulk_size=self.retrieve_bulk_size)
        self.logger.debug("Main thread get %s [submitting + submitted + running] processings to process: %s" % (len(processings), str([processing['processing_id'] for processing in processings])))
        if processings:
            self.logger.info("Main thread get %s [submitting + submitted + running] processings to process: %s" % (len(processings), str([processing['processing_id'] for processing in processings])))
        return processings

    def process_running_processing(self, processing):
        transform_id = processing['transform_id']
        input_output_maps = core_transforms.get_transform_input_output_maps(transform_id)
        work = processing['processing_metadata']['work']
        # outputs = work.poll_processing()
        processing_update, content_updates = work.poll_processing_updates(input_output_maps)

        if processing_update:
            processing_update['parameters']['locking'] = ProcessingLocking.Idle
        else:
            processing_update = {'processing_id': processing['processing_id'],
                                 'parameters': {'locking': ProcessingLocking.Idle}}

        ret = {'processing_update': processing_update,
               'content_updates': content_updates}
        return ret

    def process_running_processings(self):
        ret = []
        while not self.running_task_queue.empty():
            try:
                processing = self.running_task_queue.get()
                if processing:
                    self.logger.info("Main thread processing running processing: %s" % processing)
                    ret_processing = self.process_running_processing(processing)
                    if ret_processing:
                        ret.append(ret_processing)
            except Exception as ex:
                self.logger.error(ex)
                self.logger.error(traceback.format_exc())
        return ret

    def finish_running_processings(self):
        while not self.running_output_queue.empty():
            processing = self.running_output_queue.get()
            if processing:
                self.logger.info("Main thread processing(processing_id: %s) status changed to %s" % (processing['processing_updates']['processing_id'],
                                                                                                     processing['processing_updates']['parameters']['status']))

                self.logger.info("Main thread finishing running processing %s" % str(processing))
                core_processings.update_processing_contents(processing_update=processing['processing_update'],
                                                            content_updates=processing['content_updates'])

    def clean_locks(self):
        self.logger.info("clean locking")
        core_processings.clean_locking()

    def run(self):
        """
        Main run function.
        """
        try:
            self.logger.info("Starting main thread")

            self.load_plugins()
            self.init()

            task = self.create_task(task_func=self.get_new_processings, task_output_queue=self.new_task_queue, task_args=tuple(), task_kwargs={}, delay_time=1, priority=1)
            self.add_task(task)
            task = self.create_task(task_func=self.process_new_processings, task_output_queue=self.new_output_queue, task_args=tuple(), task_kwargs={}, delay_time=1, priority=1)
            self.add_task(task)
            task = self.create_task(task_func=self.finish_new_processings, task_output_queue=None, task_args=tuple(), task_kwargs={}, delay_time=1, priority=1)
            self.add_task(task)

            task = self.create_task(task_func=self.get_running_processings, task_output_queue=self.running_task_queue, task_args=tuple(), task_kwargs={}, delay_time=1, priority=1)
            self.add_task(task)
            task = self.create_task(task_func=self.process_running_processings, task_output_queue=self.running_output_queue, task_args=tuple(), task_kwargs={}, delay_time=1, priority=1)
            self.add_task(task)
            task = self.create_task(task_func=self.finish_running_processings, task_output_queue=None, task_args=tuple(), task_kwargs={}, delay_time=1, priority=1)
            self.add_task(task)

            task = self.create_task(task_func=self.clean_locks, task_output_queue=None, task_args=tuple(), task_kwargs={}, delay_time=1800, priority=1)
            self.add_task(task)

            self.execute()
        except KeyboardInterrupt:
            self.stop()


if __name__ == '__main__':
    agent = Carrier()
    agent()
