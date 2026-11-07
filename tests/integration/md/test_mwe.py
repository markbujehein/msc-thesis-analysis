import unittest

import numpy as np
import openmm as mm
from openmm import app, unit

from mwe import simulate


def argon_box(n=3, a=0.6):
    top = app.Topology()
    chain = top.addChain()
    system = mm.System()
    force = mm.NonbondedForce()
    force.setNonbondedMethod(mm.NonbondedForce.CutoffPeriodic)
    force.setCutoffDistance(0.8 * unit.nanometer)
    pos = []
    for i in range(n**3):
        top.addAtom("Ar", app.Element.getBySymbol("Ar"), top.addResidue("AR", chain))
        system.addParticle(39.948)
        force.addParticle(0.0, 0.34, 1.0)
        pos.append(mm.Vec3(i % n, i // n % n, i // n**2) * a)
    system.addForce(force)
    box = [mm.Vec3(n * a, 0, 0), mm.Vec3(0, n * a, 0), mm.Vec3(0, 0, n * a)]
    system.setDefaultPeriodicBoxVectors(*box)
    top.setPeriodicBoxVectors(box * unit.nanometer)
    return top, system, unit.Quantity(pos, unit.nanometer)


class SimulateTest(unittest.TestCase):
    def test_frames_shape_and_finite(self):
        top, system, pos = argon_box()
        v = simulate(top, system, pos, 10, 20, 40, 4, 1.0)
        self.assertEqual(v.shape, (10, 27, 3))
        self.assertTrue(np.isfinite(v).all())


if __name__ == "__main__":
    unittest.main()
