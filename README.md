# SliQSim Qiskit Interface - Execute SliQSim on Qiskit

## Introduction
This is a Qiskit provider for [SliQSim](https://github.com/NTU-ALComLab/SliQSim) where you can execute `SliQSim` from Qiskit framework as a backend option.

`SliQSim` is a BDD-based quantum circuit simulator implemented in C/C++ on top of [CUDD](http://web.mit.edu/sage/export/tmp/y/usr/share/doc/polybori/cudd/cuddIntro.html) package. In `SliQSim`, a bit-slicing technique based on BDDs is used to represent quantum state vectors. For more details of the simulator, please refer to the [paper](https://arxiv.org/abs/2007.09304).

## Installation
To use this provider, one should first install IBM's [Qiskit](https://github.com/Qiskit/qiskit), and then install the provider with pip.

```commandline
pip install qiskit
pip install qiskit-sliqsim-provider
```

## Execution
The gate set supported in SliQSim now contains Pauli-X (x), Pauli-Y (y), Pauli-Z (z), Hadamard (h), Phase and its inverse (s and sdg), π/8 and its inverse (t and tdg), Rotation-X with phase π/2 (rx(pi/2)), Rotation-Y with phase π/2 (ry(pi/2)), Controlled-NOT (cx), Controlled-Z (cz), Toffoli (ccx and mcx), SWAP (swap), and Fredkin (cswap).

For simulation types, we provide both weak and strong simulation options, where the weak simulation samples outcomes from the output distribution obtained after the circuit is applied, and the strong simulation calculates the resulting state vector of the quantum circuit. The following examples demostrate the usage of the provider.

```python
# Import tools
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, execute
from qiskit_sliqsim_provider import SliQSimProvider

# Initiate SliQSim Provider
provider = SliQSimProvider()

# Construct a 2-qubit bell-state circuit
qr = QuantumRegister(2)
cr = ClassicalRegister(2)
qc = QuantumCircuit(qr, cr)

qc.h(qr[0])
qc.cx(qr[0], qr[1])
qc.measure(qr, cr)

# Get the backend of weak simulation
backend = provider.get_backend('weak_simulator')

# Execute simulation
job = execute(qc, backend=backend, shots=1024)

# Obtain and print the results
result = job.result()
print(result.get_counts(qc))
```
In the above [Python code](https://github.com/NTU-ALComLab/Qiskit-SliQSim-Provider/blob/master/samples/sample.py), we construct a 2-qubit bell-state circuit with measurement gates at the end, and execute the simulator with weak simulation backend option `weak_simulator`. The sampled result is then printed:
```commandline
{'00': 523, '11': 501}
```

Circuits can also be read from files in `OpenQASM` format, which is used by Qiskit. Here we read a [circuit](https://github.com/NTU-ALComLab/SliQSim/blob/master/examples/bell_state.qasm), which is also a 2-qubit bell-state circuit but with no measurements gates, to showcase the strong simulation:
```python
qc = QuantumCircuit.from_qasm_file("../SliQSim/examples/bell_state.qasm")
```
To execute the strong simulation, the backend option `weak_simulator` is replaced with `strong_simulator`:
```python
backend = provider.get_backend('strong_simulator')
```
and after obtaining the results, we acquire the state vector instead of the counts of sampled outcomes:
```python
print(result.get_statevector(qc))
```
The state vector is then printed:
```commandline
[0.707107+0.j 0.      +0.j 0.      +0.j 0.707107+0.j]
```

One may also use our simulator by executing a compiled binary file. Check this [repo](https://github.com/NTU-ALComLab/SliQSim).


## Citation
Please cite the following paper if you use our simulator for your research:

<summary>
  <a href="https://arxiv.org/abs/2007.09304">Y. Tsai, J. R. Jiang, and C. Jhang, "Bit-Slicing the Hilbert Space: Scaling Up Accurate Quantum Circuit Simulation to a New Level," 2020, arXiv: 2007.09304</a>
</summary>

```bibtex
@misc{tsai2020bitslicing,
      title={Bit-Slicing the Hilbert Space: Scaling Up Accurate Quantum Circuit Simulation to a New Level},
      author={Yuan{-}Hung Tsai and Jie{-}Hong R. Jiang and Chiao{-}Shan Jhang},
      year={2020},
      note={arXiv: 2007.09304}
}
```

## Contact
If you have any questions or suggestions, feel free to [create an issue](https://github.com/NTU-ALComLab/SliQSim/issues), or contact us through r08943103@ntu.edu.tw.
