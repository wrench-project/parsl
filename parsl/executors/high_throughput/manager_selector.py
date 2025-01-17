import random
from abc import ABCMeta, abstractmethod
from typing import Dict, List, Set

from parsl.executors.high_throughput.manager_record import ManagerRecord


class ManagerSelector(metaclass=ABCMeta):

    @abstractmethod
    def sort_managers(self, ready_managers: Dict[bytes, ManagerRecord], manager_list: Set[bytes]) -> List[bytes]:
        """ Sort a given list of managers.

        Any operations pertaining to the sorting and rearrangement of the
        interesting_managers Set should be performed here.
        """
        pass

class RandomManagerSelector(ManagerSelector):
    def sort_managers(self, ready_managers: Dict[bytes, ManagerRecord], manager_list: Set[bytes]) -> List[bytes]:
        c_manager_list = list(manager_list)
        random.shuffle(c_manager_list)
        return c_manager_list

class MostIdleSelector(ManagerSelector):
    def sort_managers(self, ready_managers: Dict[bytes, ManagerRecord], manager_list: Set[bytes]) -> List[bytes]:
        c_manager_list = list(manager_list)
        c_manager_list.sort(key=lambda x: ready_managers[x]['max_capacity'] - len(ready_managers[x]['tasks']), reverse=True)
        return c_manager_list

class FastestManagerSelector(ManagerSelector):
    def sort_managers(self, ready_managers: Dict[bytes, ManagerRecord], manager_list: Set[bytes]) -> List[bytes]:
        c_manager_list = list(manager_list)
        c_manager_list.sort(key=lambda x: ready_managers[x]['cpu_speed'])
        return c_manager_list