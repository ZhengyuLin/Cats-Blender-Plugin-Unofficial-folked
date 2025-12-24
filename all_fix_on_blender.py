import bpy
import copy
import os
import json

def cats_fix():
    bpy.context.scene.keep_upper_chest = False
    bpy.context.scene.keep_end_bones = False
    bpy.context.scene.keep_twist_bones = False

    bpy.context.scene.fix_twist_bones = True
    bpy.context.scene.join_meshes = True
    bpy.context.scene.connect_bones = True
    bpy.context.scene.remove_zero_weight = True
    bpy.context.scene.remove_rigidbodies_joints = True

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.make_single_user(object=True, obdata=True, material=True, animation=False, obdata_animation=False)

    bpy.ops.cats_armature.fix()
    bpy.ops.cats_material.combine_mats()
    bpy.ops.cats_manual.separate_by_materials()

def fix_bone_names():
    def translate_name(name):
        return name.replace(' ', '_')

    for arm in bpy.data.armatures:
        new_name = translate_name(arm.name)
        print(f'renaming {arm.name} to {new_name}')
        arm.name = new_name

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            for bone in obj.pose.bones:
                new_name = translate_name(bone.name)
                print(f'renaming {bone.name} to {new_name}')
                bone.name = new_name
    bpy.context.view_layer.update()

def adjust_eye_bone_axis():
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE': 
            armature = obj
            break
    if not armature or armature.type != 'ARMATURE':
        raise ValueError("Armature not found")
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='EDIT')

    L_eye_bone_name = "Eye_L"
    R_eye_bone_name = "Eye_R"

    L_eye_bone = armature.data.edit_bones[L_eye_bone_name]
    R_eye_bone = armature.data.edit_bones[R_eye_bone_name]

    if L_eye_bone and R_eye_bone:
        L_head = copy.deepcopy(L_eye_bone.head)
        L_tail = copy.deepcopy(L_eye_bone.tail)
        L_tail[0] = L_head[0]
        L_tail[1] = L_head[1]
        L_tail[2] = L_head[2] + 0.03
        L_eye_bone.tail = L_tail

        R_head = copy.deepcopy(R_eye_bone.head)
        R_tail = copy.deepcopy(R_eye_bone.tail)
        R_tail[0] = R_head[0]
        R_tail[1] = R_head[1]
        R_tail[2] = R_head[2] + 0.03
        R_eye_bone.tail = R_tail
    else:
        print(f"Eye bone not found")

    bpy.ops.object.mode_set(mode='OBJECT')

def add_root_bone():
    armature = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break
    if not armature or armature.type != 'ARMATURE':
        raise ValueError("Armature not found")
    bpy.context.view_layer.objects.active = armature
    hips_bone_name = "Hips"
    root_bone_name = "Root"
    
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    hips_bone = edit_bones.get(hips_bone_name)
    if not hips_bone:
        raise Exception("未找到 hips 骨骼")
    root_bone = edit_bones.new(root_bone_name)
    root_bone.head = (0, 0, 0)  # 起点位置
    root_bone.tail = (0, 0, 0.1)  # 尾部位置（要有长度）
    root_bone.roll = 0.0
    hips_bone.parent = root_bone
    hips_bone.use_connect = False

    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"Added {root_bone_name} and parented it to {hips_bone_name}")

def fix_material():
    for obj in bpy.data.objects:
        if not obj.type == 'MESH': continue
        print(f"Mesh: {obj.name}")
        for slot in obj.material_slots:
            mat = slot.material
            if not mat: continue
            print(f"Material: {mat.name}")
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            for node in nodes:
                if node.type == 'TEX_IMAGE':
                    image = node.image
                    if image and node.name == "mmd_base_tex":
                        print(f"  Texture Node: {node.name}, Image: {image.name}, Path: {image.filepath}")
                        texture_name = image.name
            for node in nodes:
                nodes.remove(node)
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf.location = (0, 0)
            output = nodes.new(type='ShaderNodeOutputMaterial')
            output.location = (200, 0)
            img_node = nodes.new(type='ShaderNodeTexImage')
            img_node.location = (-200, 0)

            img = bpy.data.images.get(texture_name)
            if img:
                img_node.image = img

            links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
            links.new(img_node.outputs["Color"], bsdf.inputs["Base Color"])
            if ("表情" in texture_name or "facial" in texture_name) and "Alpha" in img_node.outputs:
                links.new(img_node.outputs["Alpha"], bsdf.inputs["Alpha"])

def select_children(obj: bpy.types.Object, recursive=True):
    """Select all children of the given object."""
    obj.select_set(True)
    for child in obj.children:
        child.select_set(True)
        if recursive:
            select_children(child, recursive)

cats_fix()
fix_bone_names()
adjust_eye_bone_axis()
add_root_bone()
fix_material()
selected_object = bpy.context.selected_objects[0]
select_children(obj=selected_object)
