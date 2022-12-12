# Import tools
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit_sliqsim_provider import SliQSimProvider

# Initiate SliQSim Provider
provider = SliQSimProvider()

# Construct a quantum circuit: 2-qubit bell-state
qr = QuantumRegister(2)
cr = ClassicalRegister(2)
qc = QuantumCircuit(qr, cr)

qc.h(qr[0])
qc.cx(qr[0], qr[1])
qc.measure(qr, cr)

# Read a circuit from a .qasm file
# qc = QuantumCircuit.from_qasm_file("../SliQSim/examples/bell_state.qasm")

# Get the backend of sampling simulation
backend = provider.get_backend('sampling')

# Get the backend of statevector simulation
# backend = provider.get_backend('all_amplitude')

# Execute simulation
job = execute(qc, backend=backend, shots=1024, optimization_level=0)

# Obtain and print the results
result = job.result()
print(result.get_counts(qc))
# print(result.get_statevector(qc))