#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate as gate
import opengate.contrib.phantoms.nemaiec as gate_iec
import opengate.contrib.spect.siemens_intevo as intevo
import opengate.contrib.spect.ge_discovery_nm670 as nm670
from scipy.spatial.transform import Rotation
from digitizer_helpers import add_digitizer_intevo_lu177
from pathlib import Path

if __name__ == "__main__":

    # folders
    output_folder = Path("output")
    simu_name = "test003"

    # create the simulation
    sim = gate.Simulation()

    # main options
    #sim.visu = True  # uncomment to enable visualisation
    sim.visu_type = "vrml"
    sim.random_seed = "auto"
    sim.number_of_threads = 1

    # units
    sec = gate.g4_units.s
    deg = gate.g4_units.deg
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    cm3 = gate.g4_units.cm3
    Bq = gate.g4_units.Bq
    BqmL = Bq / cm3
    keV = gate.g4_units.keV

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # spect heads
    heads = []
    crystals = []
    for i in range(2):
        head, colli, crystal = intevo.add_spect_head(
            sim, f"spect_{i}", collimator_type="melp", debug=sim.visu
        )
        heads.append(head)
        crystals.append(crystal)
    # this head translation is not used (only to avoid overlap warning at initialisation)
    heads[0].translation = [40 * cm, 0, 0]
    heads[1].translation = [-40 * cm, 0, 0]

    # phantom
    phantom = gate_iec.add_iec_phantom(sim, name='phantom', fake_material=True)

    # table
    table = nm670.add_fake_table(sim, "table")
    table.translation = [0, 31 * cm, 0]

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystals[0].name, "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystals[1].name, "all", 2 * mm)

    # add sources for all spheres
    a = 1e4 * BqmL / sim.number_of_threads
    activity_Bq_mL = [a] * 6
    sources = gate_iec.add_spheres_sources(
        sim, phantom.name, "sources", "all", activity_Bq_mL, verbose=True
    )
    for source in sources:
        gate.sources.generic.set_source_rad_energy_spectrum(source, "lu177")
        source.particle = "gamma"

    # digitizer : probably not correct
    for i in range(2):
        proj = add_digitizer_intevo_lu177(sim, heads[i].name, crystals[i].name)
        proj.output = output_folder / f"{simu_name}_projection_{i}.mhd"
        print(f'Projection size: {proj.size}')
        print(f'Projection spacing: {proj.spacing} mm')
        print(f'Projection output: {proj.output}')

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output = output_folder / f"{simu_name}_stats.txt"

    # compute the gantry rotations
    total_time = 300 * sec
    if sim.visu:
        total_time = 0.001 * sec
    n = 60
    step_time = total_time / n
    step_angle = 360 / len(heads) / n
    sim.run_timing_intervals = []
    for i in range(2):
        translations = []
        rotations = []
        initial_rot = Rotation.from_euler("X", 90, degrees=True)
        if i == 1:
            initial_rot = Rotation.from_euler("ZX", (180, 90), degrees=True)
        current_angle_deg = 20
        start_time = 0
        end_time = step_time
        for r in range(n):
            r = 40 * cm
            if i == 1:
                r = -40 * cm
            t, rot = gate.geometry.utility.get_transform_orbiting(
                [r, 0, 0], "Z", current_angle_deg
            )
            rot = Rotation.from_matrix(rot)
            rot = rot * initial_rot
            rot = rot.as_matrix()
            translations.append(t)
            rotations.append(rot)
            if i == 0:
                sim.run_timing_intervals.append([start_time, end_time])
            print(f'Add head {i}, angle {current_angle_deg} ({len(rotations)})')
            current_angle_deg += step_angle
            start_time = end_time
            end_time += step_time

        # set the motion for the SPECT head
        heads[i].add_dynamic_parametrisation(translation=translations, rotation=rotations)

    # go !
    sim.running_verbose_level = gate.logger.RUN
    sim.run()

    # print
    stats = sim.output.get_actor("stats")
    print(stats)
