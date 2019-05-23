#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

"""
@brief 

@namespace ...
@authors Reda Drissi <mohamed-reda.drissi@atos.net>
@copyright 2019  Bull S.A.S.  -  All rights reserved.
           This is not Free or Open Source software.
           Please contact Bull SAS for details about its license.
           Bull - Rue Jean Jaurès - B.P. 68 - 78340 Les Clayes-sous-Bois


Description This is a test suite for qiskit circuit converter

Overview
=========


"""
import unittest
from qat.lang.AQASM.gates import *
from qat.lang.AQASM.program import Program
from qat.interop.pyquil.converters import to_pyquil
from pyquil import Program as Prg
from pyquil import gates as pg
import numpy as np


pygates_1qb = [X, Y, Z, I, S, T, H,
               RX(3.14), RY(3.14), RZ(3.14), PH(3.14)]
pygates_2qb = [SWAP, CNOT, H.ctrl(), RZ(3.14).ctrl(),
               RY(3.14).ctrl()]

quil_1qb = [pg.X, pg.Y, pg.Z, pg.I, pg.S, pg.T, pg.H]
quil_params   = [pg.RX, pg.RY, pg.RZ, pg.PHASE]
quil_ctrl = [pg.X, pg.H]
quil_ctrl_prm = [pg.RZ, pg.RY]
def extract_syntax(circuit):
    result = []
    supername = None
    for op in circuit.ops:
        gate = circuit.gateDic[op.gate]
        ctrl = gate.nbctrls
        dag = gate.is_dag
        qubits = op.qbits
        i = 0
        while gate.subgate:
            if gate.name[0] != '_' and supername is None:
                supername = gate.name
            gate = circuit.gateDic[gate.subgate]
            if gate.is_dag:
                i += 1

        if ctrl is None or supername is not None:
            ctrl = 0
        name = 'C-'*ctrl

        if i%2 == 0:
            if dag:
                name += 'D-'
        else:
            if not dag:
                name += 'D-'
        if supername is not None:
            name += supername
        else:
            name += gate.syntax.name
        params = [ param.double_p for param in gate.syntax.parameters]
        result.append({'name': name, 'params' : params, 'qubits': qubits})
        supername = None
    return result

def print_aq(circuit):
    data = extract_syntax(circuit)
    result = ""
    for entry in data:
        result += "Gate {} with params {} on qubits {}\n".format(entry['name'], entry['params'], entry['qubits'])
        supername = None
    print(result)

class TestQiskit2QLMConversion(unittest.TestCase):
    """ Tests the function converting qiskit circuit
        to qlm circuit"""

    def test_default_gates(self):
        prog = Program()
        qreg = prog.qalloc(3)

        for op in pygates_1qb:
            prog.apply(op, qreg[0])

        for op in pygates_2qb:
            prog.apply(op, qreg[0], qreg[1])

        prog.apply(CCNOT, qreg[0], qreg[1], qreg[2])

        qlm_circuit = prog.to_circ()
        #print_aq(qlm_circuit)
        result = to_pyquil(qlm_circuit)
        #print(result)
        expected = Prg()
        for op in quil_1qb:
            expected += op(0)
        for op in quil_params:
            expected += op(3.14, 0)

        expected += pg.SWAP(0, 1)
        for op in quil_ctrl:
            expected += op(1).controlled(0)
        for op in quil_ctrl_prm:
            expected += op(3.14, 1).controlled(0)

        expected += pg.CNOT(1, 2).controlled(0)
        #print(expected)
        self.assertEqual(str(result).split('\n', 1)[1], str(expected))

    def test_recursive_ctrl_and_dagger(self):
        prog = Program()
        qreg = prog.qalloc(5)
        prog.apply(Y.ctrl().ctrl().ctrl().ctrl().dag().dag().dag(), qreg[0], qreg[1], qreg[2], qreg[3], qreg[4])
        qlm_circuit = prog.to_circ()
        result = to_pyquil(qlm_circuit)
        expected = Prg()
        expected = pg.Y(4).controlled(0).controlled(1).controlled(2).controlled(3).dagger()
        self.assertEqual(str(result).split('\n', 1)[1][:-1], str(expected))
    def test_measures(self):
        prog = Program()
        qreg = prog.qalloc(3)
        creg = prog.calloc(3)

        prog.apply(H, qreg[0])
        prog.apply(H, qreg[1])
        prog.apply(H, qreg[2])

        prog.measure(qreg, creg)

        result = to_pyquil(prog.to_circ())

        expected = Prg()
        cbs = expected.declare('creg', 'BIT', 3)
        expected += pg.H(0)
        expected += pg.H(1)
        expected += pg.H(2)
        expected += pg.MEASURE(0, cbs[0])
        expected += pg.MEASURE(1, cbs[1])
        expected += pg.MEASURE(2, cbs[2])

        #print(result)
        #print(expected)
        self.assertEqual(result, expected)
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
