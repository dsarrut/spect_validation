#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import SimpleITK as sitk
import numpy as np
from matplotlib import pyplot as plt
from pathlib import Path

if __name__ == "__main__":

    # read the reference image
    ref_img = sitk.ReadImage("y_10cm.mhd")
    ref_img_array = sitk.GetArrayFromImage(ref_img)
    print(f"Ref image = {ref_img_array.shape}")
    s = ref_img.GetSpacing()[1]
    # 4 slices : 2 x heads and 2 x energy windows
    # get the first slice = first head and peak
    ref_img_array = ref_img_array[0]
    print(f"Ref image = {ref_img_array.shape}")
    total = ref_img_array.sum()

    # dump img
    img = sitk.GetImageFromArray(ref_img_array)
    img.SetSpacing([s, s, 1])
    img.SetOrigin([0, 0, 0])
    sitk.WriteImage(img, "y_10cm_peak.mhd")

    # read the simulated image
    # f = Path("output") / "nema001"
    f = Path("output") / "nema001_5min_3e6"
    # f = Path("output") / "nema001_5min_1e6_no_sp_blur"
    # f = Path("output") / "nema001_5min_1e6_15mm_blur"
    img = sitk.ReadImage(f / "nema001_projection.mhd")
    img_array = sitk.GetArrayFromImage(img)
    print(f"Simu image = {img_array.shape}")
    # get the peak energy window
    img_array = img_array[1]
    print(f"Simu image = {img_array.shape}")
    # scaling
    scaling = total / img_array.sum()
    print(f"Scaling factor: {scaling}")
    img_array = img_array * scaling

    # dump img
    img = sitk.GetImageFromArray(img_array)
    img.SetSpacing([s, s, 1])
    img.SetOrigin([0, 0, 0])
    sitk.WriteImage(img, f / "nema001_projection_peak.mhd")

    # prepare plot
    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(15, 5))

    # get the central pixel profile
    a = 256 - 60
    b = 256 + 60
    x = np.arange(start=a, stop=b) * s
    w = 2
    c = 256
    y = np.sum(ref_img_array[c - w : c + w, a:b], axis=0)
    ax.plot(x, y, label="ref")
    y = np.sum(img_array[c - w : c + w, a:b], axis=0)
    ax.plot(x, y, label="simu")

    plt.legend()
    plt.show()
