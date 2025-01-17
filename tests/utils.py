import bpy
import numpy as np
import bmesh
"""
ADAPTED FROM MOLECULARNODES BY BRADY JOHNSTON
"""

def apply_mods(obj):
    """
    Applies the modifiers on the modifier stack
    
    This will realise the computations inside of any Geometry Nodes modifiers, ensuring
    that the result of the node trees can be compared by looking at the resulting 
    vertices of the object.
    """
    bpy.context.view_layer.objects.active = obj
    for modifier in obj.modifiers:
        bpy.ops.object.modifier_apply(modifier = modifier.name)
    



def get_verts(objs, float_decimals=2, n_verts=100, apply_modifiers=True, seed=42):
    """
    Randomly samples a specified number of vertices from a list of objects.

    Parameters
    ----------
    objs :[ object]
        List of objects from which to sample vertices.
    float_decimals : int, optional
        Number of decimal places to round the vertex coordinates, defaults to 4.
    n_verts : int, optional
        Number of vertices to sample, defaults to 100.
    apply_modifiers : bool, optional
        Whether to apply all modifiers on the object before sampling vertices, defaults to True.
    seed : int, optional
        Seed for the random number generator, defaults to 42.

    Returns
    -------
    str
        String representation of the randomly selected vertices.

    Notes
    -----
    This function randomly samples a specified number of vertices from the given object.
    By default, it applies all modifiers on the object before sampling vertices. The
    random seed can be set externally for reproducibility.

    If the number of vertices to sample (`n_verts`) exceeds the number of vertices
    available in the object, all available vertices will be sampled.

    The vertex coordinates are rounded to the specified number of decimal places
    (`float_decimals`) before being included in the output string.

    Examples
    --------
    >>> get_verts([objs], float_decimals=3, n_verts=50, apply_modifiers=True, seed=42)
    '1.234,2.345,3.456\n4.567,5.678,6.789\n...'
    """

    import random

    random.seed(seed)

    vert_list = []
    for obj in objs:
        if apply_modifiers:
            try:
                apply_mods(obj)
            except RuntimeError as ex:
                print("error in applying modifier", ex)
                return str(ex)
        vert_list.extend([(v.co.x, v.co.y, v.co.z) for v in obj.data.vertices])

    if n_verts > len(vert_list):
        n_verts = len(vert_list)

    random_verts = random.sample(vert_list, n_verts)

    verts_string = ""
    for i, vert in enumerate(random_verts):
        if i < n_verts:
            rounded = [np.round(x, float_decimals) for x in vert]
            verts_string += "{},{},{}\n".format(rounded[0], rounded[1], rounded[2])
    
    return verts_string


def remove_all_objects():
    for object in bpy.data.objects:
        try:
            
            bpy.data.objects.remove(object)

        except KeyError as e:
            print(e)
            pass
    # remove frame change
    bpy.context.scene.frame_set(0)


