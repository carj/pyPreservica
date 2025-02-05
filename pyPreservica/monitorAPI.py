"""
pyPreservica MonitorAPI module definition

A client library for the Preservica Repository Monitor API
https://us.preservica.com/api/processmonitor/documentation.html

author:     James Carr
licence:    Apache License 2.0

"""

from typing import Generator

from pyPreservica.common import *


class MonitorCategory(Enum):
    INGEST = 'Ingest'
    EXPORT = 'Export'
    DATA_MANAGEMENT = 'DataManagement'
    AUTOMATED = 'Automated'


class MonitorStatus(Enum):
    PENDING = 'Pending'
    RUNNING = 'Running'
    SUCCEEDED = 'Succeeded'
    FAILED = 'Failed'
    SUSPENDED = 'Suspended'
    RECOVERABLE = 'Recoverable'


class MessageStatus(Enum):
    INFO = 'Info'
    WARNING = 'Warning'
    ERROR = 'Error'


class MonitorAPI(AuthenticatedAPI):
    """
               A class for the Preservica Repository Process Monitor API

               https://us.preservica.com/api/processmonitor/documentation.html

                API for retrieving and updating monitoring information about processes.

       """

    def _messages_page_(self, monitor_id, maximum: int = 50, next_page: str = None, status: MessageStatus = None) -> PagedSet:
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}

        if next_page is None:
            params = {'monitor': monitor_id, 'start': int(0), 'max': maximum}
            if status:
                params['status'] = status.value
            request = self.session.get(f'{self.protocol}://{self.server}/api/processmonitor/messages', headers=headers,
                                       params=params)
        else:
            params = {'monitor': monitor_id}
            if status:
                params['status'] = status.value
            request = self.session.get(next_page, headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            response = json.loads(str(request.content.decode('utf-8')))
            value = response['value']
            if 'next' in value['paging']:
                url = value['paging']['next']
            else:
                url = None
            total_hits = int(value['paging']['totalResults'])
            has_more = False
            if url:
                has_more = True
            messages = value['messages']
            for m in messages:
                m['MonitorId'] = m.pop('mappedMonitorId')
                m['MessageId'] = m.pop('mappedId')
            return PagedSet(messages, has_more, int(total_hits), url)
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self._messages_page_(monitor_id, maximum, next_page, status)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "messages failed")

    def messages(self, monitor_id, status: MessageStatus = None) -> Generator:
        """
        List of messages for a process

        :param monitor_id:  The Process ID
        :type monitor_id:   str
        :param status:      The message status, info, warning, error etc.
        :type status:   MessageStatus
        :return:            Generator for each message, each message is a dict object
        """
        page_size = 25
        paged_set = self._messages_page_(monitor_id, maximum=page_size, next_page=None, status=status)
        for e in paged_set.results:
            yield e
        while paged_set.has_more:
            paged_set = self._messages_page_(monitor_id, maximum=page_size, next_page=paged_set.next_page, status=status)
            for e in paged_set.results:
                yield e

    def timeseries(self, monitor_id):
        """
        Get the historical record of progress for a single monitor

        :param monitor_id:  The Process ID
        :type monitor_id:   str
        :return:            List of timeseries information
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        request = self.session.get(f'{self.protocol}://{self.server}/api/processmonitor/monitors/{monitor_id}/timeseries',
                                   headers=headers)
        if request.status_code == requests.codes.ok:
            response = json.loads(str(request.content.decode('utf-8')))
            return response['value']['timeseries']
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            return self.timeseries(monitor_id)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "timeseries failed")

    def monitors(self, status: MonitorStatus = None, category: MonitorCategory = None) -> Generator:
        """
        Get a filtered list of non-abandoned process monitors

        :param status:  process status values (Pending, Running, Succeeded, Failed, Suspended, Recoverable)
        :type status:   MonitorStatus
        :param category: process categories (Ingest, Export, DataManagement, Automated)
        :type category:   MonitorCategory
        :return: Generator for each monitor
        """
        headers = {HEADER_TOKEN: self.token, 'Content-Type': 'application/json;charset=UTF-8'}
        params = {}
        if status:
            params['status'] = status.value
        if category:
            params['category'] = category.value
        request = self.session.get(f'{self.protocol}://{self.server}/api/processmonitor/monitors', headers=headers, params=params)
        if request.status_code == requests.codes.ok:
            monitors = json.loads(str(request.content.decode('utf-8')))
            for monitor in monitors['value']['monitors']:
                monitor['MonitorId'] = monitor.pop('mappedId')
                yield monitor
        elif request.status_code == requests.codes.unauthorized:
            self.token = self.__token__()
            yield from self.monitors(status, category)
        else:
            logger.error(request.content.decode('utf-8'))
            raise RuntimeError(request.status_code, "monitors failed")
