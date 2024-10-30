#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import opengate.contrib.spect.ge_discovery_nm670 as nm670
from opengate.contrib.spect.spect_helpers import add_fake_table
from spect_helpers import *
from pathlib import Path

if __name__ == "__main__":

    # folders
    simu_name = "nema001"

    # create the simulation
    sim = gate.Simulation()

    # main options
    # sim.visu = True
    sim.visu_type = "qt"
    sim.random_seed = "auto"
    sim.number_of_threads = 8
    sim.progress_bar = True
    sim.output_dir = Path("output") / simu_name

    # units
    sec = gate.g4_units.s
    min = gate.g4_units.min
    deg = gate.g4_units.deg
    mm = gate.g4_units.mm
    cm = gate.g4_units.cm
    m = gate.g4_units.m
    cm3 = gate.g4_units.cm3
    Bq = gate.g4_units.Bq
    BqmL = Bq / cm3
    keV = gate.g4_units.keV

    # acquisition param
    time = 5 * min
    activity = 3e6 * Bq / sim.number_of_threads
    activity = 1e6 * Bq / sim.number_of_threads
    if sim.visu:
        time = 1 * sec
        activity = 100 * Bq
        sim.number_of_threads = 1

    # world
    world = sim.world
    world.size = [2 * m, 2 * m, 2 * m]
    world.material = "G4_AIR"

    # spect head
    head, colli, crystal = nm670.add_spect_head(
        sim, "spect", collimator_type="lehr", debug=sim.visu, crystal_size="5/8"
    )
    nm670.rotate_gantry(head, radius=10 * cm, start_angle_deg=0)

    # phantom + (fake) table
    table = add_fake_table(sim, "table")
    table.translation = [0, 20.5 * cm, 0]
    glass_tube = add_phantom_spatial_resolution(sim, "phantom")
    glass_tube.rotation = Rotation.from_euler("Y", 3, degrees=True).as_matrix()
    glass_tube.translation = [0, 0, -2 * mm]

    # source with AA to speedup
    container = sim.volume_manager.get_volume(f"phantom_source_container")
    src = add_source_spatial_resolution(sim, "source", container, "tc99m", [head.name])
    src.activity = activity

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # digitizer : probably not correct
    digit = add_digitizer_tc99m_wip(sim, crystal.name, "digitizer", False)
    proj = digit.find_module("projection")
    proj.output_filename = f"{simu_name}_projection.mhd"
    print(f"Projection size: {proj.size}")
    print(f"Projection spacing: {proj.spacing} mm")
    print(f"Projection output: {proj.get_output_path()}")

    # add stat actor
    stats = sim.add_actor("SimulationStatisticsActor", "stats")
    stats.track_types_flag = True
    stats.output_filename = f"{simu_name}_stats.txt"

    # go
    sim.run_timing_intervals = [[0, time]]
    sim.run()

    # print
    print(stats)
