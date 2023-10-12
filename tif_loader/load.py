import bpy
from bpy.props import (StringProperty, FloatProperty,
                        PointerProperty,
                        )

import subprocess
from pathlib import Path
import os
import pip
import numpy as np
import pyopenvdb as vdb

bpy.types.Scene.path_tif = StringProperty(
        name="",
        description="RGB tif file",
        options = {'TEXTEDIT_UPDATE'},
        default="",
        maxlen=1024,
        subtype='FILE_PATH')
    
bpy.types.Scene.axes_order = StringProperty(
        name="",
        description="axes order (only z is used currently)",
        default="zyx",
        maxlen=6)
    
bpy.types.Scene.xy_size = FloatProperty(
        name="",
        description="xy physical pixel size in micrometer",
        default=1.0)
    
bpy.types.Scene.z_size = FloatProperty(
        name="z_size",
        description="z physical pixel size in micrometer",
        default=1.0)



# note that this will write a dynamically linked vdb file, so rerunning the script on a file with the same name
# in the same folder, but with different data, will change the previously loaded data.

def make_and_load_vdb(imgdata, x_ix, y_ix, z_ix, axes_order, tif, z_scale, xy_scale):
    import tifffile
    chax =  axes_order.find('c')
    if chax == -1:
    #    if len(imgdata.shape) == len(axes_order):
        imgdata = imgdata[:,:,:,np.newaxis]
        axes_order = axes_order + "c"
        # break and try with last axis (works for RGB)

    grids = []
    for ch in range(imgdata.shape[chax]):
    #    chdata = imgdata[:,:,:,ch].astype(np.float64)
        chdata = imgdata.take(indices=ch,axis=chax)
        slice_axes = axes_order.replace("c","")
        print(slice_axes)
        chdata = np.moveaxis(chdata, [slice_axes.find('x'),slice_axes.find('y'),slice_axes.find('z')],[0,1,2]).copy()
    #    chata = chdata
        
        grid = vdb.FloatGrid()
        grid.name = "channel " + str(ch)
        grid.copyFromArray(chdata)
        grids.append(grid)

    identifier = str(x_ix)+str(y_ix)+str(z_ix)
    vdb.write(str(tif.with_name(tif.stem + identifier +".vdb")), grids=grids)
    
    bpy.ops.object.volume_import(filepath=str(tif.with_name(tif.stem + identifier +".vdb")), align='WORLD', location=(0, 0, 0))
    return bpy.context.view_layer.objects.active

def load_tif(input_file, xy_scale, z_scale, axes_order):
    import tifffile
    tif = Path(input_file)

    with tifffile.TiffFile(input_file) as ifstif:
        imgdata = ifstif.asarray()
        metadata = dict(ifstif.imagej_metadata)
    if len(axes_order) != len(imgdata.shape):
        raise ValueError("axes_order length does not match data shape: " + str(imgdata.shape))

    imgdata = imgdata.astype(np.float64)
    # normalize entire space per axis
    if 'c' in axes_order:
        ch_first = np.moveaxis(imgdata, axes_order.find('c'), 0)
        for chix, chdata in enumerate(ch_first):
            ch_first[chix] /= np.max(chdata)
    else:
        imgdata /= np.max(imgdata)
    # raise Exception
    # (tif.parents[0] / "tmp_zstacker/").mkdir(exist_ok=True)

    # 2048 is maximum grid size for Eevee rendering, so grids are split for multiple
    xyz = [axes_order.find('x'),axes_order.find('y'),axes_order.find('z')]
    n_splits = [(imgdata.shape[dim] // 2048)+ 1 for dim in xyz]
    arrays = [imgdata]


    # Loops over all axes and splits based on length
    # reassembles in negative coordinates, parents all to a parent at (half_x, half_y, bottom) that is then translated to (0,0,0)
    volumes =[]
    a_chunks = np.array_split(imgdata, n_splits[0], axis=axes_order.find('x'))
    for a_ix, a_chunk in enumerate(a_chunks):
        b_chunks = np.array_split(a_chunk, n_splits[1], axis=axes_order.find('y'))
        for b_ix, b_chunk in enumerate(b_chunks):
            c_chunks = np.array_split(b_chunk, n_splits[2], axis=axes_order.find('z'))
            for c_ix, c_chunk in enumerate(reversed(c_chunks)):
                vol = make_and_load_vdb(c_chunk, a_ix, b_ix, c_ix, axes_order, tif, z_scale, xy_scale)
                bbox = np.array([c_chunk.shape[xyz[0]],c_chunk.shape[xyz[1]],c_chunk.shape[xyz[2]]])
                scale = np.array([1,1,z_scale/xy_scale])*0.02
                vol.scale = scale
                print(c_ix, b_ix, a_ix)
                offset = np.array([a_ix,b_ix,c_ix])
                
                vol.location = tuple(offset*bbox*scale)
                volumes.append(vol)


    # recenter x, y, keep z at bottom
    center = np.array([0.5,0.5,0]) * np.array([c_chunk.shape[xyz[0]] * (len(a_chunks)), c_chunk.shape[xyz[1]] * (len(b_chunks)), c_chunk.shape[xyz[2]] * (len(c_chunks)*(z_scale/xy_scale))])
    empty = bpy.ops.object.empty_add(location=tuple(center*0.02))

    empty = bpy.context.view_layer.objects.active
    empty.name = str(tif.name) + " container" 

    for vol in volumes:
        vol.parent = empty
        vol.matrix_parent_inverse = empty.matrix_world.inverted()

    empty.location = (0,0,0)

    print('done')
    return



