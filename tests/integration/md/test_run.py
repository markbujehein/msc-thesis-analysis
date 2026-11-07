import numpy as np
import openmm as mm
from openmm import app, unit

from run import VelocityReporter, run


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


def test_reporter_writes_float32_frames_at_interval(tmp_path):
    top, system, pos = argon_box()
    sim = app.Simulation(top, system, mm.VerletIntegrator(1 * unit.femtosecond))
    sim.context.setPositions(pos)
    sim.context.setVelocitiesToTemperature(10 * unit.kelvin)
    path = tmp_path / "v.f32"
    reporter = VelocityReporter(path, 5)
    sim.reporters.append(reporter)
    sim.step(50)
    reporter.close()
    v = np.fromfile(path, dtype=np.float32).reshape(-1, 27, 3)
    assert v.shape == (10, 27, 3)


def test_short_run_has_finite_energies(tmp_path):
    top, system, pos = argon_box()
    run(top, system, pos, 10, 1.0, 20, 40, 4, tmp_path / "v.f32", tmp_path / "log.csv")
    v = np.fromfile(tmp_path / "v.f32", dtype=np.float32).reshape(-1, 27, 3)
    assert v.shape == (10, 27, 3) and np.isfinite(v).all()
    log = np.genfromtxt(tmp_path / "log.csv", delimiter=",", names=True)
    assert np.isfinite(log["Total_Energy_kJmole"]).all()


class FakeBar:
    """Same shape as mo.status.progress_bar: a context manager with update(increment)."""

    def __init__(self, total, title):
        self.total, self.title, self.done = total, title, 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def update(self, increment=1):
        self.done += increment


def test_step_with_progress_takes_exactly_n_steps_and_reports_them():
    from run import step_with_progress

    top, system, pos = argon_box()
    sim = app.Simulation(top, system, mm.VerletIntegrator(1 * unit.femtosecond))
    sim.context.setPositions(pos)
    bars = []

    def bar(total, title):
        bars.append(FakeBar(total, title))
        return bars[-1]

    step_with_progress(sim, 25, "test", chunk=10, bar=bar)  # chunks 10, 10, 5
    assert sim.currentStep == 25
    assert (bars[0].total, bars[0].title, bars[0].done) == (25, "test", 25)


def test_step_with_progress_works_without_a_bar():
    from run import step_with_progress

    top, system, pos = argon_box()
    sim = app.Simulation(top, system, mm.VerletIntegrator(1 * unit.femtosecond))
    sim.context.setPositions(pos)
    step_with_progress(sim, 7, "test", chunk=3)
    assert sim.currentStep == 7
