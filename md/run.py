import openmm as mm
from openmm import app, unit

from progress import NoBar


def step_with_progress(simulation, n, desc, chunk=1000, bar=NoBar):
    """simulation.step(n) in chunks of `chunk` steps.

    bar(total, title) must give a context manager with update(increment),
    e.g. lambda total, title: mo.status.progress_bar(total=total, title=title).
    """
    with bar(n, desc) as progress:
        for done in range(0, n, chunk):
            m = min(chunk, n - done)
            simulation.step(m)
            progress.update(m)


class VelocityReporter:
    """Appends the velocities (nm/ps, float32) of every atom to a raw file every `every` steps.

    Read back with np.fromfile(path, dtype=np.float32).reshape(-1, n_atoms, 3).
    """

    def __init__(self, path, every):
        self._file = open(path, "wb")  # noqa: SIM115 (stays open between reports)
        self._every = every
        self._start = None

    def describeNextReport(self, simulation):
        if self._start is None:
            self._start = simulation.currentStep
        steps = self._every - (simulation.currentStep - self._start) % self._every
        return (steps, False, True, False, False)

    def report(self, simulation, state):
        v = state.getVelocities(asNumpy=True).value_in_unit(unit.nanometer / unit.picosecond)
        v.astype("float32").tofile(self._file)

    def close(self):
        self._file.close()


def run(topology, system, positions, temperature_K, dt_fs, equil_steps, prod_steps, every, velocity_path, log_path, bar=NoBar):
    """Minimise, equilibrate with Langevin, then run NVE (Verlet) and write the velocities.

    bar is passed to step_with_progress. log_path gets step, time, energies and temperature every `every` steps over the whole run.
    """
    dt = dt_fs * unit.femtosecond
    temperature = temperature_K * unit.kelvin

    integrator = mm.CompoundIntegrator()
    integrator.addIntegrator(mm.LangevinMiddleIntegrator(temperature, 1 / unit.picosecond, dt))
    integrator.addIntegrator(mm.VerletIntegrator(dt))
    integrator.setCurrentIntegrator(0)

    simulation = app.Simulation(topology, system, integrator)
    simulation.context.setPositions(positions)
    simulation.reporters.append(
        app.StateDataReporter(
            str(log_path), every, step=True, time=True, potentialEnergy=True,
            kineticEnergy=True, totalEnergy=True, temperature=True, separator=",",
        )
    )
    simulation.minimizeEnergy()
    simulation.context.setVelocitiesToTemperature(temperature)
    step_with_progress(simulation, equil_steps, "equilibration (Langevin)", bar=bar)

    integrator.setCurrentIntegrator(1)  # NVE: no thermostat while the velocities are written
    reporter = VelocityReporter(velocity_path, every)
    simulation.reporters.append(reporter)
    step_with_progress(simulation, prod_steps, "production (NVE)", bar=bar)
    reporter.close()
