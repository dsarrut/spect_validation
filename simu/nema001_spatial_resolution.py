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
    sim.number_of_threads = 4
    sim.progress_bar = True
    sim.output_dir = Path("output") / simu_name

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

    # acquisition param
    time = 30 * sec
    activity = 5e6 * Bq / sim.number_of_threads
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
        sim, "spect", collimator_type="lehr", debug=sim.visu
    )
    nm670.rotate_gantry(head, radius=10 * cm, start_angle_deg=0)

    # phantom
    table = add_fake_table(sim, "table")
    table.translation = [0, 20.5 * cm, 0]
    phantom = add_phantom_spatial_resolution(sim, "phantom")

    # source
    src = add_source_spatial_resolution(sim, "source", phantom, "tc99m", [head.name])
    src.activity = activity

    # physics
    sim.physics_manager.physics_list_name = "G4EmStandardPhysics_option3"
    sim.physics_manager.set_production_cut("world", "all", 10 * mm)
    sim.physics_manager.set_production_cut("phantom", "all", 2 * mm)
    sim.physics_manager.set_production_cut(crystal.name, "all", 2 * mm)

    # digitizer : probably not correct
    digit = nm670.add_digitizer_tc99m(sim, crystal.name, "digitizer")
    ew = digit.find_module("energy_window")
    ew.channels = [
        {"name": f"scatter", "min": 114 * keV, "max": 126 * keV},
        {"name": f"peak140", "min": 126.45 * keV, "max": 154.55 * keV},
    ]
    proj = digit.find_module("projection")
    proj.output_filename = f"{simu_name}_projection.mhd"
    proj.size = [512, 512]
    proj.spacing = [1.1049 * mm, 1.1049 * mm]
    proj.input_digi_collections = [c["name"] for c in ew.channels]
    proj.write_to_disk = True
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
