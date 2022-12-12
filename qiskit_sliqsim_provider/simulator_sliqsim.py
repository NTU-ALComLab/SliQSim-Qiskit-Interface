from qiskit.providers import BaseBackend
import subprocess
import random
import uuid
import time
import json
import abc
import os
import platform
import logging
from qiskit.providers.models import BackendConfiguration, BackendStatus
from qiskit.result import Result
from .sliqsimjob import SliQSimJob
from .sliqsimerror import SliQSimError

logger = logging.getLogger(__name__)


class SliQSimWrapper:

    def __init__(self, exe=None, mode='sv'):
        self.shots = 1
        self.seed = 0
        self.exec = exe
        self.mode = mode

    def set_config(self, global_config):
        if hasattr(global_config, 'seed'):
            self.seed = global_config.seed
        else:
            self.seed = random.getrandbits(32)

    def run(self, qasm):
        cmd = [self.exec,
               '--sim_qasm',
               '--seed={}'.format(self.seed)
               ]
        if self.mode == 'sv':
            cmd.append('--type=1')
        elif self.mode == 'qasm':
            cmd.append('--type=0')
            cmd.append('--shots={}'.format(self.shots))
        else:
            raise SliQSimError(
                'Unsupported simulation mode: {}'.format(self.mode))
        output = subprocess.check_output(
            cmd, input=qasm, stderr=None, universal_newlines=True)
        return output

    def convert_statevector_data(self, statevector):
        return [self.to_qiskit_complex(statevector[i])
                for i in range(len(statevector))]

    def convert_counts(self, counts):
        result = {}
        for qubits, count in counts.items():
            clbits = self.qubits_to_clbits(qubits)
            if clbits is not None:
                result[clbits] = result.get(clbits, 0) + count
        return result

    def qubits_to_clbits(self, qubits):
        clbits = qubits
        s = "".join(clbits)[::1]
        if s == '':
            return None
        return hex(int(s, 2))

    def to_qiskit_complex(self, num_string):
        # first obtain an actual number
        num = complex(num_string.replace('i', 'j'))
        return [num.real, num.imag]

    def parse_output(self, run_output):
        result = json.loads(run_output)
        if 'counts' in result:
            result['counts'] = self.convert_counts(
                result['counts'])
        if 'statevector' in result:
            result['statevector'] = self.convert_statevector_data(result['statevector'])
        return result

    def run_experiment(self, config, experiment):
        self.set_config(config)
        # do this before running so we can output warning to the user as soon as possible if needed
        self.start_time = time.time()
        qasm = self.convert_qobj_circuit_to_qasm(experiment)
        run_output = self.run(qasm)
        self.end_time = time.time()
        output_data = self.parse_output(run_output)
        result_dict = {'header': {'name': experiment.header.name,
                                  'memory_slots': experiment.config.memory_slots,
                                  'creg_sizes': experiment.header.creg_sizes
                                  },
                       'status': 'DONE', 'time_taken': self.end_time - self.start_time,
                       'seed': self.seed, 'shots': self.shots,
                       'data': output_data,
                       'success': True
                       }
        return result_dict

    def convert_operation_to_line(self, op, qubit_names, clbit_names):
        """convert one operation from the qobj file to a QASM line in the format SliQSim can handle"""
        name_string = op.name
        qubits_string = ", ".join([qubit_names[i] for i in op.qubits])
        if hasattr(op, 'params') and len(op.params) > 0:
            denominator = round(3.14159/op.params[0])
            if denominator not in [2,-2]:
                raise Exception('Only rx/ry(+-pi/2) are supported yet. Make sure that the circuit is made up by supported gates and the optimization is turned off.')
            if denominator==2:
                params_string = '(pi/2)'
            elif denominator==-2:
                params_string = '(-pi/2)'
        else:
            params_string = ""
        if name_string == "measure":  # special syntax
            return "measure {} -> {};".format(qubit_names[op.qubits[0]], clbit_names[op.memory[0]])
        return "{}{} {};".format(name_string, params_string, qubits_string)

    def convert_qobj_circuit_to_qasm(self, experiment):
        instructions = experiment.instructions
        qubit_num = len(experiment.header.qubit_labels)
        clbit_num = len(experiment.header.clbit_labels)
        qubit_names = ['q[{}]'.format(i) for i in range(qubit_num)]
        clbit_names = ['c[{}]'.format(i) for i in range(clbit_num)]
        qasm_file_lines = ["OPENQASM 2.0;",
                           "qreg q[{}];".format(qubit_num),
                           "creg c[{}];".format(qubit_num)
                           ]
        for op in instructions:
            qasm_file_lines.append(self.convert_operation_to_line(
                op, qubit_names, clbit_names))
        qasm_content = "\n".join(qasm_file_lines) + "\n"
        return qasm_content



class SimulatorBase(BaseBackend, abc.ABC):
    DEFAULT_CONFIGURATION = {
        'coupling_map': None,
        'backend_name': None,
        'backend_version': '1.0',
        'url': 'https://github.com/NTU-ALComLab/Qiskit-SliQSim-Provider',
        'simulator': True,
        'local': True,
        'description': 'SliQSim C++ simulator',
        'basis_gates': ['cx', 'x', 'y', 'z', 'h', 's', 't', 'sdg', 'tdg', 'rx', 'ry', 'cz', 'ccx', 'mcx', 'swap', 'cswap'],
        'memory': False,
        'n_qubits': 30,
        'conditional': False,
        'max_shots': 100000,
        'open_pulse': False,
        'gates': [
            {
                'name': 'TODO',
                'parameters': [],
                'qasm_def': 'TODO'
            }
        ]
    }

    EXTENSION = '.exe' if platform.system() == 'Windows' else ''

    DEFAULT_SIMULATOR_PATHS = [
    # This is the path where make creates  the binary
    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                 '../build/lib/qiskit_sliqsim_provider/SliQSim'
                                 + EXTENSION)),
    # This is the path where PIP installs the simulator
    os.path.abspath(os.path.join(os.path.dirname(__file__),
                                 './SliQSim' + EXTENSION)),
]
    def __init__(self, configuration=None, provider=None):
        """
        Args:
            configuration (dict): backend configuration
        Raises:
             ImportError: if the simulator is not available.
        """
        super().__init__(configuration=(configuration or
                                        BackendConfiguration.from_dict(self.DEFAULT_CONFIGURATION)),
                         provider=provider)

        paths = self.DEFAULT_SIMULATOR_PATHS
        # Ensure that the executable is available.
        try:
            self.executable = next(
                path for path in paths if os.path.exists(path))
        except:
            print(paths)
            raise FileNotFoundError('Simulator executable not found')

    def run(self, qobj):
        job_id = str(uuid.uuid4())
        local_job = SliQSimJob(self, job_id, self._run_job, qobj)
        local_job.submit()
        return local_job

    def status(self):
        """Return backend status.

        Returns:
            BackendStatus: the status of the backend.
        """
        return BackendStatus(backend_name=self.name(),
                             backend_version=self.configuration().backend_version,
                             operational=True,
                             pending_jobs=0,
                             status_msg='')

    @abc.abstractclassmethod
    def _run_job(self, job_id, qobj):
        return NotImplemented

    @abc.abstractclassmethod
    def _validate(self, qobj):
        return NotImplemented


class QasmSimulator(SimulatorBase):

    def _run_job(self, job_id, qobj):
        """Run circuits in q_job"""
        result_list = []
        self._validate(qobj)
        s = SliQSimWrapper(self.executable, mode='qasm')
        s.shots = qobj.config.shots
        start = time.time()
        for experiment in qobj.experiments:
            result_list.append(s.run_experiment(qobj.config, experiment))
        end = time.time()
        result = {'backend_name': 'sampling',
                  'backend_version': self._configuration.backend_version,
                  'qobj_id': qobj.qobj_id,
                  'job_id': job_id,
                  'results': result_list,
                  'status': 'COMPLETED',
                  'success': True,
                  'time_taken': (end - start)}
        return Result.from_dict(result)

    def _validate(self, qobj):
        for experiment in qobj.experiments:
            name = experiment.header.name
            if experiment.config.memory_slots == 0:
                logger.warning('No classical registers in circuit "%s", '
                               'counts will be empty.', name)
            elif 'measure' not in [op.name for op in experiment.instructions]:
                logger.warning('No measurements in circuit "%s", '
                               'classical register will remain all zeros.', name)


class StatevectorSimulator(SimulatorBase):

    def _run_job(self, job_id, qobj):
        """Run circuits in q_job"""
        result_list = []
        self._validate(qobj)
        s = SliQSimWrapper(self.executable, mode='sv')
        s.shots = qobj.config.shots
        start = time.time()
        for experiment in qobj.experiments:
            result_list.append(s.run_experiment(qobj.config, experiment))
        end = time.time()
        result = {'backend_name': 'all_amplitude',
                  'backend_version': self._configuration.backend_version,
                  'qobj_id': qobj.qobj_id,
                  'job_id': job_id,
                  'results': result_list,
                  'status': 'COMPLETED',
                  'success': True,
                  'time_taken': (end - start)}
        return Result.from_dict(result)

    def _validate(self, qobj):
        if qobj.config.shots != 1:
            logger.info('"%s" only supports 1 shot. Setting shots=1.',
                        self.name())
            qobj.config.shots = 1
        for experiment in qobj.experiments:
            name = experiment.header.name
            if getattr(experiment.config, 'shots', 1) != 1:
                logger.info('"%s" only supports 1 shot. '
                            'Setting shots=1 for circuit "%s".',
                            self.name(), name)
                experiment.config.shots = 1
