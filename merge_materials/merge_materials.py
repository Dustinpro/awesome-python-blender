# Merge materials of a 3D CAD model (.obj) and create a uv mapping image
#  Usage: blender -b --python ./merge_materials.py
#  Platform: Blender 2.8x
#  Author: Chao Xu (chaoxu@ucla.edu)

# comment the line below if you copy the codes to the python console of Blender GUI
import bpy

# input setup
obj_folder_path = './sample/models'
obj_name = 'model_normalized'

if not obj_folder_path.endswith('/'):
    obj_folder_path = obj_folder_path + '/'
    
full_input_path = obj_folder_path + obj_name + '.obj'
full_output_path = obj_folder_path + obj_name + '_merged.obj'

# delete default cube and import our shape
bpy.data.objects['Cube'].select_set(True)
bpy.ops.object.delete()
bpy.ops.import_scene.obj(filepath = full_input_path)

context = bpy.context
scene = context.scene
vl = context.view_layer
# deselect all to make sure select one at a time
bpy.ops.object.select_all(action='DESELECT')

# find the mesh obj
for each_obj in scene.objects:
    if (each_obj.type == 'MESH'):
        obj = each_obj
        break

# uv mapping
vl.objects.active = obj
obj.select_set(True)
# print(obj.name)
lm = obj.data.uv_layers.new(name="LightMap")
lm.active = True
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.lightmap_pack()

# create the output image
bpy.ops.image.new(name="merged_lightmap", width=512, height=512)

for slot in obj.material_slots:
    nodes = slot.material.node_tree.nodes
    node = nodes.new('ShaderNodeTexImage')
    node.name = 'Merged Lightmap'
    node.image = bpy.data.images['merged_lightmap']
    nodes.active = node

# start the rendering engine to bake the texture
scene.render.engine = 'CYCLES'
scene.cycles.device = 'GPU'
# bake configuration
scene.cycles.bake_type = 'DIFFUSE'
scene.render.bake.use_pass_direct = False
scene.render.bake.use_pass_indirect = False
obj.select_set(True)
bpy.ops.object.bake(type = 'DIFFUSE')
# save the merged texture image
bpy.data.images['merged_lightmap'].filepath_raw = obj_folder_path+"merged_lightmap.png"
bpy.data.images['merged_lightmap'].file_format = 'PNG'
bpy.data.images['merged_lightmap'].save()

# link material nodes to the merged texture image
for slot in obj.material_slots:
    node_tree = slot.material.node_tree
    nodes = node_tree.nodes
    node_lightmap = nodes.get('Merged Lightmap')
    node_bsdf = nodes.get('Principled BSDF')
    node_tree.links.new(node_bsdf.inputs.get('Base Color'), node_lightmap.outputs.get('Color'))

# export the CAD model in the .obj format
bpy.context.object.data.uv_layers["LightMap"].active_render = True
bpy.ops.export_scene.obj(filepath = full_output_path)
