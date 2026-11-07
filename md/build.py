import numpy as np
import openmm as mm
from openff.toolkit import Molecule, Topology
from openmm import app, unit
from openmmforcefields.generators import SystemGenerator
from rdkit import Chem, RDLogger
from rdkit.Chem import AllChem

from progress import NoBar

HBAR_MEV_PS = 0.6582119569  # meV ps


def read_pdb(path):
    """PDB file (with a CRYST1 box) as an openmm PDBFile."""
    return app.PDBFile(str(path))


def bonds_from_geometry(path, smiles, bar=NoBar):
    """One openff Molecule per molecule in the PDB.

    RDKit finds the bonds from the geometry; the SMILES template fixes the bond orders.
    """
    geometry = Chem.MolFromPDBFile(str(path), removeHs=False, proximityBonding=True)
    template = Chem.AddHs(Chem.MolFromSmiles(smiles))
    RDLogger.DisableLog("rdApp.warning")  # symmetric molecules: harmless "more than one match" warning
    molecules = []
    fragments = Chem.GetMolFrags(geometry, asMols=True)
    with bar(len(fragments), "assigning bond orders") as progress:
        for fragment in fragments:
            fixed = AllChem.AssignBondOrdersFromTemplate(template, fragment)
            molecules.append(Molecule.from_rdkit(fixed, allow_undefined_stereo=True))
            progress.update(1)
    RDLogger.EnableLog("rdApp.warning")
    return molecules


def make_system(path, smiles, cutoff_nm, bar=NoBar):
    """Flexible (no constraints) periodic GAFF2 system. Returns topology, system, positions."""
    pdb = read_pdb(path)
    molecules = bonds_from_geometry(path, smiles, bar=bar)
    topology = Topology.from_molecules(molecules).to_openmm()
    topology.setPeriodicBoxVectors(pdb.topology.getPeriodicBoxVectors())

    generator = SystemGenerator(
        forcefields=[],
        small_molecule_forcefield="gaff-2.11",
        molecules=[molecules[0]],  # identical molecules: one template is enough
        forcefield_kwargs={"constraints": None, "rigidWater": False},
        periodic_forcefield_kwargs={
            "nonbondedMethod": app.PME,
            "nonbondedCutoff": cutoff_nm * unit.nanometer,
        },
    )
    system = generator.create_system(topology)
    # a smooth cutoff: without it the energy jumps at the cutoff and no true minimum (Hessian) is found
    nonbonded = next(f for f in system.getForces() if isinstance(f, mm.NonbondedForce))
    nonbonded.setUseSwitchingFunction(True)
    nonbonded.setSwitchingDistance((cutoff_nm - 0.1) * unit.nanometer)
    nonbonded.setUseDispersionCorrection(True)
    return topology, system, pdb.positions


def oh_energy_mev(topology, system):
    """Harmonic energy hbar*sqrt(k/mu) of the first O-H bond, in meV."""
    atoms = list(topology.atoms())
    force = next(f for f in system.getForces() if isinstance(f, mm.HarmonicBondForce))
    for i, j, _, k in (force.getBondParameters(n) for n in range(force.getNumBonds())):
        if {atoms[i].element.symbol, atoms[j].element.symbol} == {"O", "H"}:
            m_i = system.getParticleMass(i).value_in_unit(unit.amu)
            m_j = system.getParticleMass(j).value_in_unit(unit.amu)
            mu = m_i * m_j / (m_i + m_j)
            # 1 kJ/mol = 1 amu nm^2/ps^2, so sqrt(k/mu) is in rad/ps
            return HBAR_MEV_PS * np.sqrt(k.value_in_unit(unit.kilojoule_per_mole / unit.nanometer**2) / mu)
    raise ValueError("no O-H bond in the system")
