#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0OA
#
# Authors:
# - Wen Guan, <wen.guan@cern.ch>, 2019 - 2020

"""
Constants.
"""

from enum import Enum


SCOPE_LENGTH = 25
NAME_LENGTH = 255


class Sections:
    Main = 'main'
    Common = 'common'
    Clerk = 'clerk'
    Marshaller = 'marshaller'
    Transformer = 'transformer'
    Transporter = 'transporter'
    Carrier = 'carrier'
    Conductor = 'conductor'


class HTTP_STATUS_CODE:
    OK = 200
    Created = 201
    Accepted = 202

    # Client Errors
    BadRequest = 400
    Unauthorized = 401
    Forbidden = 403
    NotFound = 404
    NoMethod = 405
    Conflict = 409

    # Server Errors
    InternalError = 500


class IDDSEnum(Enum):
    def to_dict(self):
        ret = {'class': self.__class__.__name__,
               'module': self.__class__.__module__,
               'attributes': {}}
        for key, value in self.__dict__.items():
            if not key.startswith('__'):
                if key == 'logger':
                    value = None
                if value and hasattr(value, 'to_dict'):
                    value = value.to_dict()
                ret['attributes'][key] = value
        return ret

    @staticmethod
    def is_class(d):
        if d and isinstance(d, dict) and 'class' in d and 'module' in d and 'attributes' in d:
            return True
        return False

    @staticmethod
    def load_instance(d):
        module = __import__(d['module'], fromlist=[None])
        cls = getattr(module, d['class'])
        if issubclass(cls, Enum):
            impl = cls(d['attributes']['_value_'])
        else:
            impl = cls()
        return impl

    @staticmethod
    def from_dict(d):
        if IDDSEnum.is_class(d):
            impl = IDDSEnum.load_instance(d)
            for key, value in d['attributes'].items():
                if key == 'logger':
                    continue
                if IDDSEnum.is_class(value):
                    value = IDDSEnum.from_dict(value)
                setattr(impl, key, value)
            return impl
        return d


class WorkStatus(IDDSEnum):
    New = 0
    Ready = 1
    Transforming = 2
    Finished = 3
    SubFinished = 4
    Failed = 5
    Extend = 6
    ToCancel = 7
    Cancelling = 8
    Cancelled = 9


class RequestStatus(IDDSEnum):
    New = 0
    Ready = 1
    Transforming = 2
    Finished = 3
    SubFinished = 4
    Failed = 5
    Extend = 6
    ToCancel = 7
    Cancelling = 8
    Cancelled = 9


class RequestLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class WorkprogressStatus(IDDSEnum):
    New = 0
    Ready = 1
    Transforming = 2
    Finished = 3
    SubFinished = 4
    Failed = 5
    Extend = 6
    ToCancel = 7
    Cancelling = 8
    Cancelled = 9


class WorkprogressLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class RequestType(IDDSEnum):
    Workflow = 0
    EventStreaming = 1
    StageIn = 2
    ActiveLearning = 3
    HyperParameterOpt = 4
    Derivation = 5
    Other = 99


class TransformType(IDDSEnum):
    Workflow = 0
    EventStreaming = 1
    StageIn = 2
    ActiveLearning = 3
    HyperParameterOpt = 4
    Derivation = 5
    Other = 99


class TransformStatus(IDDSEnum):
    New = 0
    Ready = 1
    Transforming = 2
    Finished = 3
    SubFinished = 4
    Failed = 5
    Extend = 6
    ToCancel = 7
    Cancelling = 8
    Cancelled = 9


class TransformLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class CollectionType(IDDSEnum):
    Container = 0
    Dataset = 1
    File = 2
    PseudoDataset = 3


class CollectionRelationType(IDDSEnum):
    Input = 0
    Output = 1
    Log = 2


class CollectionStatus(IDDSEnum):
    New = 0
    Updated = 1
    Processing = 2
    Open = 3
    Closed = 4
    SubClosed = 5
    Failed = 6
    Deleted = 7


class CollectionLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class ContentType(IDDSEnum):
    File = 0
    Event = 1
    PseudoContent = 2


class ContentStatus(IDDSEnum):
    New = 0
    Processing = 1
    Available = 2
    Failed = 3
    FinalFailed = 4
    Lost = 5
    Deleted = 6
    Mapped = 7


class ContentLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class GranularityType(IDDSEnum):
    File = 0
    Event = 1


class ProcessingStatus(IDDSEnum):
    New = 0
    Submitting = 1
    Submitted = 2
    Running = 3
    Finished = 4
    Failed = 5
    Lost = 6
    Cancel = 7
    FinishedOnStep = 8
    FinishedOnExec = 9
    TimeOut = 10
    FinishedTerm = 11


class ProcessingLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class MessageType(IDDSEnum):
    StageInFile = 0
    StageInCollection = 1
    ActiveLearningFile = 2
    ActiveLearningCollection = 3
    HyperParameterOptFile = 4
    HyperParameterOptCollection = 5
    UnknownFile = 98
    UnknownCollection = 99


class MessageStatus(IDDSEnum):
    New = 0
    Fetched = 1
    Delivered = 2


class MessageLocking(IDDSEnum):
    Idle = 0
    Locking = 1


class MessageSource(IDDSEnum):
    Clerk = 0
    Transformer = 1
    Transporter = 2
    Carrier = 3
    Conductor = 4
