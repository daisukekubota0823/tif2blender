import bpy
import pathlib
from .. import pkg
from bpy.types import AddonPreferences


ADDON_DIR = pathlib.Path(__file__).resolve().parent.parent


bpy.types.Scene.pypi_mirror_provider = bpy.props.StringProperty(
    name='pypi_mirror_provider',
    description='PyPI Mirror Provider (normally leave blank, BFSU or TUNA for Beijing)',
    options={'TEXTEDIT_UPDATE', 'LIBRARY_EDITABLE'},
    default='Default',
    subtype='NONE',
    # search=pkg.get_pypi_mirror_alias,
)


# Defines the preferences panel for the addon, which shows the buttons for
# installing and reinstalling the required python packages defined in 'requirements.txt'
class Tif2BlenderPreferences(AddonPreferences):
    bl_idname = 'tif2blender'

    def draw(self, context):
        layout = self.layout
        layout.label(text="Install the required packages for tif2blender.")

        col_main = layout.column(heading='', align=False)
        row_import = col_main.row()
        row_import.prop(bpy.context.scene,
                        'pypi_mirror_provider', text='Set PyPI Mirror')

        pkgs = pkg.get_pkgs()
        for package in pkgs.values():
            row = layout.row()
            col = row.column()
            row = col.row()
            pkg.button_install_pkg(
                layout=row,
                name=package.get('name'),
                version=package.get('version'),
                desc=package.get('desc')
            )