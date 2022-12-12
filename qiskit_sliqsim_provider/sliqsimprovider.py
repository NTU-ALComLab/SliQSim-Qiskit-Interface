from qiskit.providers import BaseProvider
from .simulator_sliqsim import QasmSimulator, StatevectorSimulator


class SliQSimProvider(BaseProvider):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

        # Populate the list of local SliQSim backends.
        self.backends_list = {'sampling': QasmSimulator(provider=self),
                              'all_amplitude': StatevectorSimulator(provider=self)
                              }

    def get_backend(self, name='sampling', **kwargs):
        return self.backends_list[name]

    def available_backends(self, filters=None):
        # pylint: disable=arguments-differ
        backends = self.backends_list

        filters = filters or {}
        for key, value in filters.items():
            backends = {name: instance for name, instance in backends.items()
                        if instance.configuration().get(key) == value}

        return list(backends.values())

    def backends(self, name=None, **kwargs):
        return list(self.backends_list.values())

    def __str__(self):
        return 'SliQSimProvider'
